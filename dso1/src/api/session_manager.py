import threading
import time
import os
import sys
import queue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from session import EvaluationThread, load_delegues, load_single_product, save_conversation, update_delegue_score, _score_to_level, conversation_loop, TOKEN_FACTORY_URL
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
        eval_thread.join(timeout=10)

        cv_summary = eval_thread.get_summary()
        session_path = save_conversation(delegue, messages, cv_summary)

        if cv_summary:
            new_score = cv_summary.get("averages", {}).get("performance", 0.0)
            new_level = _score_to_level(new_score)
            update_delegue_score(delegue, new_score, new_level)
            self.last_results = cv_summary
            
        try:
            from report_generator import generate_report
            self.last_report = generate_report(delegue, messages, cv_summary, session_path)
            # Make the path relative to ROOT_DIR so we can serve it
            if self.last_report:
                import pathlib
                report_p = pathlib.Path(self.last_report)
                self.last_report = report_p.name  # just the filename
        except Exception:
            pass

        self.is_active = False

    def stop_session(self):
        if not self.is_active or not self.eval_thread:
            return {"status": "no_active_session"}
        
        # Debloquer le Push-to-Talk pour permettre à la boucle de conversation de se terminer
        try:
            from avatar.stt import recording_start_event, recording_stop_event
            recording_stop_event.set()
            recording_start_event.set()
        except ImportError:
            pass

        # Stopping evaluation thread will make conversation_loop break eventually
        self.eval_thread.stop()
        return {"status": "stopping"}

    def get_current_frame(self):
        if self.eval_thread and self.eval_thread.current_frame is not None:
            return self.eval_thread.current_frame
        return None

manager = TrainingSessionManager()
