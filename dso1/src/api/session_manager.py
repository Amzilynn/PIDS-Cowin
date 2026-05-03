import threading
import time
import os
import sys
import queue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from session import EvaluationThread, load_delegues, load_single_product, update_delegue_score, _score_to_level, conversation_loop, TOKEN_FACTORY_URL
from openai import OpenAI
from nlp.rag.retriever import Retriever
from nlp.rag.rag_build import load_or_build_rag
from dotenv import load_dotenv

env_path = os.path.join(SRC_DIR, "..", ".env")
load_dotenv(dotenv_path=env_path)

class TrainingSessionManager:
    def __init__(self):
        self.eval_thread = None
        self.conv_thread = None
        self.is_active = False
        self.client = None
        self.retriever = None
        self.delegue = None
        self.product = None
        self.message_queue = queue.Queue()
        self.last_results = None
        self.last_report = None

    def initialize_models(self):
        if not self.client:
            api_key = os.getenv("TOKENFACTORY_API_KEY")
            self.client = OpenAI(api_key=api_key, base_url=TOKEN_FACTORY_URL)
        if not self.retriever:
            store = load_or_build_rag()
            self.retriever = Retriever(store)

    def start_session(self, delegue_id: int, product_id: int = None):
        if self.is_active:
            raise ValueError("Une session est déjà en cours.")

        delegues = load_delegues()
        self.delegue = next((d for d in delegues if d["id"] == delegue_id), None)
        if not self.delegue:
            raise ValueError(f"Délégué {delegue_id} introuvable.")
            
        self.product = load_single_product(product_id) if product_id else None

        self.initialize_models()

        # Nettoyage de l'état
        while not self.message_queue.empty():
            self.message_queue.get()
        self.last_results = None
        self.last_report = None
        self.should_discard = False
        
        # Enregistrer l'heure de début pour le calcul de durée
        from datetime import datetime
        self.session_start_time = datetime.utcnow()

        self.eval_thread = EvaluationThread(delegue_nom=self.delegue["nom"])
        self.eval_thread.use_api = True # No cv2.imshow
        self.eval_thread.api_mode_hud_off = True # Cache le dessin CV pour être pro
        self.eval_thread.start()
        
        # We need a wrapped conversation loop that runs in a thread
        self.conv_thread = threading.Thread(
            target=self._run_conversation,
            args=(self.delegue, self.eval_thread, self.client, self.retriever, self.product),
            daemon=True
        )
        self.conv_thread.start()
        self.is_active = True
        return {"status": "started", "delegue": self.delegue["nom"]}

    def _run_conversation(self, delegue, eval_thread, client, retriever, product):
        def _on_msg(role, content):
            self.message_queue.put({"role": "user" if role == "user" else "bot", "content": content})

        try:
            messages = conversation_loop(
                delegue, eval_thread, client, retriever,
                product=product,
                on_message_callback=_on_msg
            )
        except Exception as e:
            print(f"[Api Session Error] {e}")
            messages = []
            
        print("\n[Api Main] Fermeture du pipeline CV...")
        eval_thread.set_avatar_speaking(False)
        eval_thread.stop()
        
        if self.should_discard:
            print("[Api Main] Session ANNULÉE. Pas d'enregistrement en base.")
            if self.eval_thread == eval_thread:
                self.is_active = False
            return

        # On marque la session comme inactive pour les flux temps réel
        
        # On marque la session comme inactive pour les flux temps réel
        if self.eval_thread == eval_thread:
            self.is_active = False 
            
        # Attendre la fin du thread CV (timeout genereux pour Windows)
        eval_thread.join(timeout=60)

        # Si le thread est encore vivant apres 60s, on l'attend encore un peu
        import time as _time
        for _ in range(20):  # Max 10s supplementaires
            cv_summary = eval_thread.get_summary()
            if cv_summary is not None:
                break
            _time.sleep(0.5)

        if cv_summary is None:
            print("[Api Main] WARN: cv_summary toujours None apres 70s, on continue sans.")
            cv_summary = {}

        # ── NLP Fact-Checking Evaluation ──
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages and product:
            print(f"[Api Main] Evaluation NLP en cours sur {len(user_messages)} message(s) utilisateur...")
            try:
                # On retire les mots-cles techniques de fin de session
                filtered_messages = [
                    m for m in messages
                    if m.get("role") in ("user", "assistant")
                    and m.get("content", "").lower().strip() not in ["stop", "fin", "terminer", "quitter", "annuler"]
                ]

                if filtered_messages:
                    from evaluation.nlp_evaluator import NLPEvaluator
                    evaluator = NLPEvaluator(client)
                    nlp_report = evaluator.evaluate_session(filtered_messages, product)
                    cv_summary["nlp"] = nlp_report
                    print(f"[Api Main] NLP OK — score produit: {nlp_report.get('product_knowledge_score')}")
                else:
                    print("[Api Main] Aucun message substantiel a evaluer.")
            except Exception as e:
                import traceback
                print(f"[Api Main] Erreur NLP Evaluator: {e}")
                traceback.print_exc()
        else:
            reason = "aucun message utilisateur" if not user_messages else "aucun produit selectionne"
            print(f"[Api Main] NLP skipped: {reason}")

        # (Plus de sauvegarde JSON locale - tout va en base SQL)

        if cv_summary:
            new_score = cv_summary.get("averages", {}).get("performance", 0.0)
            new_level = _score_to_level(new_score)
            update_delegue_score(delegue, new_score, new_level)
        # Toujours mettre a jour last_results (meme si vide) pour que /stop retourne quelque chose
        self.last_results = cv_summary

        # ── Persistance SQL ───────────────────────────────────────────────────
        try:
            from db_session_saver import save_simulation_to_db
            sim_id = save_simulation_to_db(
                delegue    = delegue,
                product    = product,
                messages   = messages,
                cv_summary = cv_summary,
                start_time = getattr(self, 'session_start_time', None),
            )
            if sim_id:
                self.last_results = {**(cv_summary or {}), "simulation_id": sim_id}
        except Exception as e:
            import traceback
            print(f"[DB Save] Erreur persistance SQL: {e}")
            traceback.print_exc()
            
        try:
            from report_generator import generate_report
            self.last_report = generate_report(delegue, messages, cv_summary)
            if self.last_report:
                import pathlib
                report_file = pathlib.Path(self.last_report).name
                self.last_report = report_file
                # Mettre à jour la base avec le nom du fichier rapport
                if sim_id:
                    from db_session_saver import update_simulation_report_path
                    update_simulation_report_path(sim_id, report_file)
        except Exception as e:
            print(f"[Report] Erreur: {e}")
            pass

        # On marque la session comme terminee seulement ICI pour que le /stop attende tout.
        self.is_active = False 

    def stop_session(self, discard=False):
        if not self.eval_thread:
            self.is_active = False
            return {"status": "no_active_session"}
        
        self.should_discard = discard
        self.is_active = False

        # Debloquer le nouvel STT textuel pour permettre à la boucle de conversation de se terminer
        try:
            from avatar.stt import set_user_text
            set_user_text("annuler" if discard else "stop")
        except ImportError:
            pass

        # Stopping evaluation thread will make conversation_loop break eventually
        self.eval_thread.stop()
        return {"status": "stopping" if not discard else "cancelled"}

    def get_current_frame(self):
        if self.eval_thread and self.eval_thread.is_alive() and self.eval_thread.current_frame is not None:
            return self.eval_thread.current_frame
        return None

manager = TrainingSessionManager()
