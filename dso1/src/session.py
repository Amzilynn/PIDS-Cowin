"""
session.py — Orchestrateur principal de session Co-Win / Vital Lab
═══════════════════════════════════════════════════════════════════

Deux threads :
  Thread 1 (EvaluationThread) — caméra OpenCV + body / face / tone EN CONTINU
  Thread main (conversation_loop) — STT (Whisper) → Groq+RAG → TTS (Edge-TTS)

Règle micro :
  • ToneAnalyzer (PyAudio) ne s'arrête JAMAIS.
  • Whisper (sounddevice) et ToneAnalyzer coexistent grâce au mode partagé WASAPI.
  • Quand l'avatar parle (TTS) → flag avatar_speaking=True :
      - Le HUD continue d'afficher les données en temps réel
      - Les frames NE sont PAS loggées (score non faussé par la voix de l'avatar)
  • Quand le délégué parle → avatar_speaking=False :
      - Les frames sont loggées normalement
      - L'analyse tonale porte sur la voix du délégué

Lancement :
    python session.py
"""

import csv
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# ── Projet local ──────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.database import SessionLocal
from shared.models import Delegate, Product, Gamme

from avatar.prompts import SYSTEM_PROMPT
from avatar.stt     import get_user_text
from avatar.voice   import speak_text

from nlp.rag.rag_build  import load_or_build_rag
from nlp.rag.retriever  import Retriever

from evaluation import (
    BodyLanguageAnalyzer,
    FaceEmotionAnalyzer,
    ToneAnalyzer,
    FusionScorer,
    SessionSnapshot,
    SessionLogger,
)

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

AVATAR_MODEL     = "hosted_vllm/Llama-3.1-70B-Instruct"
TOKEN_FACTORY_URL = "https://tokenfactory.esprit.tn/api"
CAMERA_INDEX    = 0
FRAME_WIDTH     = 1280
FRAME_HEIGHT    = 720

# Chemins relatifs à la racine de dso1 (parent de src)
ROOT_DIR        = Path(__file__).resolve().parent.parent
SESSIONS_DIR    = ROOT_DIR / "sessions"
DATA_DIR        = ROOT_DIR / "Data"

MAX_SESSION_MIN = 30          # durée max (minutes)

STOP_KEYWORDS = {
    "fin", "terminer", "stop", "end", "quitter", "exit", "quit",
    "arrêter", "arreter",
}

PRODUCT_KEYWORDS = [
    "produit", "product", "médicament", "medicine", "drug",
    "présenter", "present", "proposer", "propose",
    "comprimé", "capsule", "sirop", "complément",
    "indication", "posologie", "dosage", "traitement", "effet",
    "principe actif", "composition", "contre-indication",
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — Database
# ═══════════════════════════════════════════════════════════════════════════════

def load_delegues() -> list[dict]:
    db = SessionLocal()
    try:
        delegues = db.query(Delegate).all()
        return [
            {
                "id":    d.id,
                "nom":   f"{d.first_name} {d.last_name}",
                "level": d.current_level,
                "score": int(d.global_score),
                "role":  d.role
            }
            for d in delegues
        ]
    finally:
        db.close()


def load_products() -> list[dict]:
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [
            {
                "id":   p.id,
                "name": p.name,
                "gamme_id": p.gamme_id,
                "gamme_name": p.gamme.name if p.gamme else "Sans Gamme"
            }
            for p in products
        ]
    finally:
        db.close()

def load_gammes() -> list[dict]:
    db = SessionLocal()
    try:
        gammes = db.query(Gamme).all()
        return [
            {
                "id": g.id,
                "name": g.name
            }
            for g in gammes
        ]
    finally:
        db.close()

def load_single_product(product_id: int) -> dict | None:
    if not product_id: return None
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if p:
            return {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "indications": p.indications,
                "compositions": p.compositions,
                "usage_advice": p.usage_advice
            }
        return None
    finally:
        db.close()

def update_delegue_score(delegue: dict, new_score: float, new_level: str) -> None:
    """Met à jour score + niveau dans la base de données."""
    db = SessionLocal()
    try:
        d = db.query(Delegate).filter(Delegate.id == delegue["id"]).first()
        if d:
            d.global_score = new_score * 100
            d.current_level = new_level
            db.commit()
            print(f"[SQL] {d.first_name} -> score={int(d.global_score)}/100  level={new_level}")
    finally:
        db.close()


def _score_to_level(score: float) -> str:
    if score >= 0.85: return "Expert"
    if score >= 0.65: return "Confirmé"
    if score >= 0.40: return "Junior"
    return "Débutant"


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — RAG
# ═══════════════════════════════════════════════════════════════════════════════

def should_use_rag(text: str) -> bool:
    return any(kw in text.lower() for kw in PRODUCT_KEYWORDS)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — HUD OpenCV
# ═══════════════════════════════════════════════════════════════════════════════

def _score_color(score: float) -> tuple:
    if score >= 0.70: return (80, 220, 80)
    if score >= 0.45: return (80, 200, 250)
    return (80, 80, 240)


def draw_hud(
    frame: np.ndarray,
    snap: SessionSnapshot,
    delegue_nom: str,
    conv_turn: int,
    avatar_speaking: bool,
) -> np.ndarray:
    """Affiche le HUD de métriques en temps réel sur la frame caméra."""
    h, w = frame.shape[:2]

    # Sidebar semi-transparente
    overlay = frame.copy()
    cv2.rectangle(overlay, (w - 300, 0), (w, h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)

    x, y = w - 285, 28

    def put(text, color=(210, 210, 210), scale=0.55):
        nonlocal y
        cv2.putText(frame, text, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
        y += 24

    # En-tête
    put(f"  {delegue_nom.upper()} — tour {conv_turn}", (100, 200, 255), 0.54)

    # Indicateur avatar parle / délégué parle
    if avatar_speaking:
        put("  🔊 Avatar parle...", (255, 200, 60), 0.50)
    else:
        put("  🎤 Délégué évalué", (60, 220, 120), 0.50)
    y += 2

    # Scores globaux
    put(f"Performance:  {snap.performance_score:.0%}", _score_color(snap.performance_score))
    put(f"Confiance:    {snap.confidence_score:.0%}",  _score_color(snap.confidence_score))
    put(f"Stress:       {snap.stress_score:.0%}",      _score_color(1 - snap.stress_score))
    put(f"Engagement:   {snap.engagement_score:.0%}",  _score_color(snap.engagement_score))

    # Corps
    y += 6
    put("── CORPS ──", (170, 170, 170), 0.48)
    if snap.body:
        put(f"Posture:   {snap.body.posture_score:.0%}")
        put(f"Ouverture: {snap.body.openness_score:.0%}")
        put(f"Agitation: {snap.body.fidget_score:.0%}")
        put(f"Inclin:    {snap.body.lean}")
    else:
        put("Pas de corps détecté", (120, 120, 255))

    # Visage
    y += 6
    put("── VISAGE ──", (170, 170, 170), 0.48)
    if snap.face and snap.face.face_detected:
        put(f"Émotion:  {snap.face.dominant_emotion}")
        put(f"Contact:  {'OUI' if snap.face.eye_contact else 'NON'}")
    else:
        put("Pas de visage", (120, 120, 255))

    # Voix
    y += 6
    put("── VOIX ──", (170, 170, 170), 0.48)
    if snap.tone and snap.tone.tone_label != "unknown":
        put(f"Ton:    {snap.tone.tone_label}")
        put(f"Pauses: {snap.tone.pause_ratio:.0%}")
    else:
        put("En attente audio...", (120, 120, 255))

    # Feedback textuel
    y += 8
    words = snap.summary.split()
    line, lines = "", []
    for wd in words:
        if len(line + wd) > 30:
            lines.append(line.strip()); line = wd + " "
        else:
            line += wd + " "
    if line:
        lines.append(line.strip())
    put("── FEEDBACK ──", (100, 255, 180), 0.48)
    for ln in lines[:4]:
        put(ln, (190, 220, 190), 0.46)

    return frame


# ═══════════════════════════════════════════════════════════════════════════════
# THREAD 1 — EvaluationThread
# ═══════════════════════════════════════════════════════════════════════════════

class EvaluationThread(threading.Thread):
    """
    Pipeline CV qui tourne TOUTE la session, sans jamais s'arrêter.

    Comportement du logging :
      - avatar_speaking = False  → frames loggées  (délégué évalué)
      - avatar_speaking = True   → frames affichées MAIS non loggées
                                   (voix avatar ne fausse pas les scores)

    Le ToneAnalyzer (PyAudio) tourne en continu.
    Il coexiste avec Whisper (sounddevice) via le mode partagé WASAPI Windows.
    """

    def __init__(self, delegue_nom: str):
        super().__init__(daemon=True, name="EvalThread")
        self.delegue_nom = delegue_nom

        self._stop_event      = threading.Event()
        self._avatar_speaking = threading.Event()  # set = avatar parle
        self._conv_turn       = 0
        self._summary: dict | None = None

        # Modules CV
        self.body_analyzer  = BodyLanguageAnalyzer()
        self.face_analyzer  = FaceEmotionAnalyzer(backend="efficientnet", skip_frames=3)
        self.tone_analyzer  = ToneAnalyzer()
        self.fusion_scorer  = FusionScorer()
        self.session_logger = SessionLogger(output_dir=str(SESSIONS_DIR))
        self.use_api        = False
        self.api_mode_hud_off = False
        self.current_frame  = None
        self.current_snap   = None

    # ── API publique ─────────────────────────────────────────────────────────

    def stop(self):
        """Signal d'arrêt propre."""
        self._stop_event.set()

    def set_avatar_speaking(self, speaking: bool):
        """
        Appelé depuis la boucle conversationnelle.
        True  → TTS en cours, ne pas loguer les frames.
        False → délégué parle, loguer normalement.
        """
        if speaking:
            self._avatar_speaking.set()
        else:
            self._avatar_speaking.clear()

    def set_conv_turn(self, n: int):
        self._conv_turn = n

    def get_summary(self) -> dict | None:
        return self._summary

    @property
    def csv_path(self) -> Path:
        return self.session_logger.csv_path

    @property
    def json_path(self) -> Path:
        return self.session_logger.json_path

    # ── Boucle principale ────────────────────────────────────────────────────

    def run(self):
        # Utilise MSMF sur Windows car DSHOW est extremement lent pour l'ouverture
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_MSMF)
        if not cap.isOpened():
            cap = cv2.VideoCapture(CAMERA_INDEX)
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print("[EvalThread] ❌ Impossible d'ouvrir la caméra.")
            return

        # ToneAnalyzer démarre une fois et reste actif toute la session
        self.tone_analyzer.start()
        start_time = time.time()
        print("[EvalThread] ✅ Pipeline CV démarré — évaluation en continu.")

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.03)
                    continue

                ts_ms = (time.time() - start_time) * 1000

                # ── Analyse des 3 modules ────────────────────────────────────
                body_result = self.body_analyzer.analyze(frame)
                face_result = self.face_analyzer.analyze(frame)
                tone_result = self.tone_analyzer.get_result()

                # ── Fusion ───────────────────────────────────────────────────
                snap = self.fusion_scorer.fuse(
                    ts_ms, body_result, face_result, tone_result
                )

                # ── Overlays visuels ─────────────────────
                if not self.api_mode_hud_off:
                    self.body_analyzer.draw_landmarks(frame)
                    self.face_analyzer.draw_overlay(frame, face_result)

                avatar_speaking = self._avatar_speaking.is_set()
                if not self.api_mode_hud_off:
                    frame = draw_hud(
                        frame, snap,
                        self.delegue_nom, self._conv_turn,
                        avatar_speaking,
                    )
                
                self.current_frame = frame.copy()
                self.current_snap = {
                    "performance_score": snap.performance_score,
                    "confidence_score": snap.confidence_score,
                    "stress_score": snap.stress_score,
                    "engagement_score": snap.engagement_score
                }

                if not self.use_api:
                    cv2.imshow("Co-Win | Évaluation délégué", frame)
                    # Touche Q pour fermer
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self._stop_event.set()
                        break

                # ── Loguer UNIQUEMENT quand c'est le délégué qui parle ───────
                if not avatar_speaking:
                    self.session_logger.log(snap)

        finally:
            print("[EvalThread] Arrêt du pipeline CV...")
            self.tone_analyzer.stop()
            self.body_analyzer.close()
            self.face_analyzer.close()
            cap.release()
            cv2.destroyAllWindows()
            self._summary = self.session_logger.close()
            grade = self._summary.get("grade", "N/A") if self._summary else "N/A"
            print(f"[EvalThread] Grade session : {grade}")


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — Groq
# ═══════════════════════════════════════════════════════════════════════════════

def ask_avatar(client: OpenAI, messages: list) -> str | None:
    try:
        response = client.chat.completions.create(
            model=AVATAR_MODEL,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM Error] {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# BOUCLE CONVERSATIONNELLE (thread principal)
# ═══════════════════════════════════════════════════════════════════════════════

def conversation_loop(
    delegue: dict,
    eval_thread: EvaluationThread,
    client: OpenAI,
    retriever: Retriever,
    product: dict = None,
    on_message_callback: callable = None
) -> list[dict]:
    """
    Boucle principale STT → Groq → TTS.
    Signale à EvaluationThread quand c'est l'avatar qui parle
    afin de geler le logging pendant ce temps.
    """
    level    = delegue["level"]
    role     = "doctor" if delegue["role"] == "Medical" else "pharmacist"
    
    system_prompt = SYSTEM_PROMPT.format(level=level, role=role)
    
    # ── INJECTION DB PRODUIT ──
    if product:
        system_prompt += f"\n\nYOU MUST BASE YOUR ROLEPLAY AND OBJECTIONS ON THE FOLLOWING PRODUCT DATA SHEET:\n"
        system_prompt += f"- Name: {product.get('name', 'Unknown')}\n"
        system_prompt += f"- Indications: {product.get('indications') or 'Not provided'}\n"
        system_prompt += f"- Active Ingredients / Composition: {product.get('compositions') or 'Not provided'}\n"
        system_prompt += f"- Usage Advice / Posology: {product.get('usage_advice') or 'Not provided'}\n"
        system_prompt += "Ensure your roleplay is strictly consistent with the medical indications and composition provided above.\n"
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    turn          = 0
    session_start = time.time()
    max_seconds   = MAX_SESSION_MIN * 60

    print(f"\n[Conv] Session démarrée — {delegue['nom']} (niveau: {level})")
    print("[Conv] Dites 'fin' ou 'stop' pour terminer.\n")
    print("─" * 50)

    while True:

        # ── Garde-fous ───────────────────────────────────────────────────────
        if time.time() - session_start > max_seconds:
            print(f"\n[Conv] Durée max ({MAX_SESSION_MIN} min) atteinte.")
            break
        if not eval_thread.is_alive():
            print("[Conv] Pipeline CV terminé — fin de session.")
            break

        # ── PHASE 1 : Délégué parle → évaluation active ──────────────────────
        eval_thread.set_avatar_speaking(False)   # ← logging actif
        print("\n🎤 En attente de votre message (Web Speech API)...")

        try:
            user_input, lang = get_user_text()
        except KeyboardInterrupt:
            print("\n[Conv] Interruption clavier.")
            break
        except Exception as e:
            print(f"[STT Error] {e}")
            continue

        if not user_input:
            print("[Conv] Aucun texte détecté, réessayez.")
            continue

        # Si le message est un signal d'arrêt ou d'annulation (envoyé par l'API stop/cancel)
        if user_input.lower() in ["stop", "annuler"]:
            print(f"[Conv] Signal d'arrêt reçu ({user_input}). Sortie de boucle.")
            break

        print(f"🗣️  Délégué : {user_input}")
        if on_message_callback:
            on_message_callback("user", user_input)

        # On n'arrête plus par mots-clés, le frontend gère la fin via l'API.

        turn += 1
        eval_thread.set_conv_turn(turn)

        # ── RAG conditionnel ─────────────────────────────────────────────────
        messages_to_send = list(messages)
        if should_use_rag(user_input):
            try:
                docs = retriever.retrieve(user_input, k=3)
                if docs:
                    messages_to_send.append({
                        "role": "system",
                        "content": (
                            "CONTEXTE PRODUIT (à utiliser UNIQUEMENT si le délégué "
                            "parle clairement de ce produit, sinon ignore) :\n"
                            + "\n".join(docs)
                        ),
                    })
            except Exception as e:
                print(f"[RAG Warning] {e}")

        messages_to_send.append({"role": "user", "content": user_input})

        # ── Appel LLM (TokenFactory) ─────────────────────────────────────────
        avatar_reply = ask_avatar(client, messages_to_send)
        if avatar_reply is None:
            print("[Conv] Pas de réponse Groq.")
            continue

        print(f"🤖 Avatar : {avatar_reply}")
        if on_message_callback:
            on_message_callback("assistant", avatar_reply)
        print("─" * 50)

        # ── PHASE 2 : Avatar parle → geler le logging ────────────────────────
        eval_thread.set_avatar_speaking(True)    # ← logging gelé
        try:
            speak_text(avatar_reply, lang)       # bloquant (attend fin du son)
        except Exception as e:
            print(f"[TTS Error] {e}")
        finally:
            eval_thread.set_avatar_speaking(False)  # ← logging reprend

        # ── Historique conversation ──────────────────────────────────────────
        messages.append({"role": "user",      "content": user_input})
        messages.append({"role": "assistant", "content": avatar_reply})

    return messages


# (save_conversation removed - everything now goes to SQL)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 55)
    print("   🩺  Co-Win — Laboratoire Vital | Session IA")
    print("═" * 55 + "\n")

    # ── 1. Sélection du délégué ──────────────────────────────────────────────
    delegues = load_delegues()
    print("Délégués disponibles :\n")
    for d in delegues:
        print(f"  [{d['id']}] {d['nom']:20s}  niveau={d['level']:15s}  score={d['score']}")

    try:
        choice  = int(input("\nChoisir un délégué (numéro) : "))
        delegue = next((d for d in delegues if d["id"] == choice), None)
        if delegue is None:
            print("Délégué introuvable.")
            return
    except (ValueError, KeyboardInterrupt):
        print("\nAnnulé.")
        return

    print(f"\n✅  {delegue['nom']} sélectionné — niveau {delegue['level']}\n")

    # ── 2. Init LLM (TokenFactory) + RAG ────────────────────────────────────
    api_key = os.getenv("TOKENFACTORY_API_KEY")
    if not api_key:
        print("[Erreur] TOKENFACTORY_API_KEY manquant dans .env")
        return
    client = OpenAI(api_key=api_key, base_url=TOKEN_FACTORY_URL)

    print("[Init] Chargement du RAG...")
    store     = load_or_build_rag()
    retriever = Retriever(store)
    print("[Init] RAG prêt ✅\n")

    # ── 3. Lancer le thread d'évaluation CV ──────────────────────────────────
    eval_thread = EvaluationThread(delegue_nom=delegue["nom"])
    eval_thread.start()
    time.sleep(1.5)   # laisser la caméra s'initialiser

    # ── 4. Boucle conversationnelle (thread principal) ────────────────────────
    try:
        messages = conversation_loop(delegue, eval_thread, client, retriever)
    except KeyboardInterrupt:
        print("\n[Main] Interruption clavier.")
        messages = []

    # ── 5. Arrêt propre ───────────────────────────────────────────────────────
    print("\n[Main] Fermeture du pipeline CV...")
    eval_thread.set_avatar_speaking(False)  # s'assurer que le logging reprend
    eval_thread.stop()
    eval_thread.join(timeout=10)

    cv_summary = eval_thread.get_summary()

    # (Local JSON saving skipped)

    # ── 7. Mise à jour score délégué ──────────────────────────────────────────
    if cv_summary:
        new_score = cv_summary.get("averages", {}).get("performance", 0.0)
        new_level = _score_to_level(new_score)
        update_delegue_score(delegue, new_score, new_level)

    # ── 8. Rapport PDF ────────────────────────────────────────────────────────
    try:
        from report_generator import generate_report
        report_path = generate_report(
            delegue      = delegue,
            messages     = messages,
            cv_summary   = cv_summary
        )
        print(f"\n[Rapport] PDF → {report_path}")
    except ImportError:
        print("[Rapport] report_generator.py absent — rapport PDF ignoré.")
    except Exception as e:
        print(f"[Rapport] Erreur : {e}")

    # ── Résumé final ─────────────────────────────────────────────────────────
    print("\n" + "═" * 55)
    if cv_summary:
        avgs = cv_summary.get("averages", {})
        print(f"  Grade       : {cv_summary.get('grade', 'N/A')}")
        print(f"  Performance : {avgs.get('performance', 0):.1%}")
        print(f"  Confiance   : {avgs.get('confidence', 0):.1%}")
        print(f"  Stress      : {avgs.get('stress', 0):.1%}")
        print(f"  Engagement  : {avgs.get('engagement', 0):.1%}")
        print(f"  Contact œil : {cv_summary.get('eye_contact_rate', 0):.1%}")
        print(f"  Émotion dom.: {cv_summary.get('dominant_emotion', 'N/A')}")
        print(f"  Ton dominant: {cv_summary.get('dominant_tone', 'N/A')}")
    print("═" * 55)
    print("  Au revoir ! 👋")
    print("═" * 55 + "\n")


if __name__ == "__main__":
    main()