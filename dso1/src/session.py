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
import queue
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv
from groq import Groq

# ── Projet local ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from avatar.prompts import SYSTEM_PROMPT
from avatar.stt     import record_audio, get_model
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

GROQ_MODEL      = "llama-3.3-70b-versatile"
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
# HELPERS — Délégués CSV
# ═══════════════════════════════════════════════════════════════════════════════

def load_delegues() -> list[dict]:
    path = DATA_DIR / "delegues.csv"
    if not path.exists():
        raise FileNotFoundError(f"[Erreur] {path} introuvable.")
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {
                "id":    int(row["Id"]),
                "nom":   row["Nom"],
                "type":  row["Type"],
                "level": row["Level"],
                "score": int(row["Score"]),
            }
            for row in csv.DictReader(f)
        ]


def update_delegue_score(delegue: dict, new_score: float, new_level: str) -> None:
    """Met à jour score + niveau dans delegues.csv."""
    path     = DATA_DIR / "delegues.csv"
    delegues = load_delegues()
    for d in delegues:
        if d["id"] == delegue["id"]:
            d["score"] = int(new_score * 100)
            d["level"] = new_level
            break
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Id", "Nom", "Type", "Level", "Score"])
        writer.writeheader()
        for d in delegues:
            writer.writerow({
                "Id": d["id"], "Nom": d["nom"], "Type": d["type"],
                "Level": d["level"], "Score": d["score"]
            })
    print(f"[CSV] {delegue['nom']} → score={int(new_score*100)}/100  level={new_level}")


def _score_to_level(score: float) -> str:
    if score >= 0.75: return "Expert"
    if score >= 0.50: return "Intermediate"
    return "Beginner"


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

def ask_avatar(client: Groq, messages: list) -> str | None:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=120,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq Error] {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# BOUCLE CONVERSATIONNELLE (thread principal)
# ═══════════════════════════════════════════════════════════════════════════════

def conversation_loop(
    delegue: dict,
    eval_thread: EvaluationThread,
    client: Groq,
    retriever: Retriever,
    delegate_type: str,
    user_input_queue: queue.Queue = None,
    on_message_callback: callable = None
) -> list[dict]:

    """
    Boucle principale STT → Groq → TTS.
    Signale à EvaluationThread quand c'est l'avatar qui parle
    afin de geler le logging pendant ce temps.
    """
    level    = delegue["level"]
    messages = [{
    "role": "system",
    "content": SYSTEM_PROMPT.format(
        level=level,
        delegate_type=delegate_type
    )
}]

    
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

        # ── PHASE 1 : Attente d'entrée (Texte ou Vocale) ─────────────────────
        eval_thread.set_avatar_speaking(False)   # ← logging actif
        
        user_input = ""
        lang = "fr"

        if user_input_queue is not None:
            print("\n⏳ En attente d'entrée (clavier ou micro via bouton)...")
            msg = user_input_queue.get()  # Bloque jusqu'à un message
            
            if msg.get("type") == "text":
                user_input = msg.get("content", "").strip()
                print(f"⌨️  Délégué (Chat) : {user_input}")
            elif msg.get("type") == "voice_trigger":
                print("\n🎤 Bouton micro pressé — En écoute...")
                try:
                    audio, _fs = record_audio()
                    model = get_model()
                    result = model.transcribe(audio, fp16=False, language="fr")
                    user_input = result.get("text", "").strip()
                    lang = result.get("language", "fr")
                    print(f"🗣️  Délégué (Vocal) : {user_input}")
                except Exception as e:
                    print(f"[Voice Error] {e}")
                    continue
        else:
            # Mode automatique original (pour CLI)
            print("\n🎤 En écoute automatique...")
            try:
                audio, _fs = record_audio()
                model      = get_model()
                result     = model.transcribe(audio, fp16=False, language="fr")
                user_input = result.get("text", "").strip()
                lang       = result.get("language", "fr")
                print(f"🗣️  Délégué : {user_input}")
            except Exception as e:
                print(f"[STT Error] {e}")
                continue

        if not user_input:
            print("[Conv] Aucun message, on continue.")
            continue

        if on_message_callback:
            on_message_callback("user", user_input)

        # ── Mot-clé de fin ───────────────────────────────────────────────────
        if any(kw in user_input.lower() for kw in STOP_KEYWORDS):
            print("[Conv] Mot-clé de fin détecté.")
            break

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

        # ── Appel Groq ───────────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════════════════════════
# SAUVEGARDE SESSION JSON
# ═══════════════════════════════════════════════════════════════════════════════

def save_conversation(delegue: dict, messages: list, cv_summary: dict | None) -> Path:
    SESSIONS_DIR.mkdir(exist_ok=True)
    nom  = delegue["nom"].replace(" ", "_")
    date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = SESSIONS_DIR / f"{nom}_{date}.json"

    session = {
        "delegue":       delegue,
        "date":          datetime.now().isoformat(),
        "conversation":  messages,
        "cv_evaluation": cv_summary,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    print(f"[Session] Conversation → {path}")
    return path


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

    print(f"\n✅  {delegue['nom']} sélectionné — type {delegue['type']} — niveau {delegue['level']}\n")

    # ── 2. Init Groq + RAG ───────────────────────────────────────────────────
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("[Erreur] GROQ_API_KEY manquant dans .env")
        return
    client = Groq(api_key=groq_key)

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
        messages = conversation_loop(
            delegue, eval_thread, client, retriever,
            delegate_type=delegue["type"]
        )
    except KeyboardInterrupt:
        print("\n[Main] Interruption clavier.")
        messages = []

    # ── 5. Arrêt propre ───────────────────────────────────────────────────────
    print("\n[Main] Fermeture du pipeline CV...")
    eval_thread.set_avatar_speaking(False)  # s'assurer que le logging reprend
    eval_thread.stop()
    eval_thread.join(timeout=10)

    cv_summary = eval_thread.get_summary()

    # ── 6. Sauvegarde ─────────────────────────────────────────────────────────
    session_path = save_conversation(delegue, messages, cv_summary)

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
            cv_summary   = cv_summary,
            session_path = session_path,
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
