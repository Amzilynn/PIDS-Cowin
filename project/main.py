import requests
import csv
import json
import os
import threading
from datetime import datetime
from evaluation.evaluator import evaluate
from agent.prompts import SYSTEM_PROMPT
from agent.voice import speak_text
from agent.stt import speech_to_text
import time
from rag.rag_build import load_or_build_rag
from rag.retriever import Retriever


tts_lock = threading.Lock()


# ─── Chargement des délégués ───────────────────────────────────────────────

def load_delegues():
    try:
        delegues = []
        with open(os.path.join("Data", "delegues.csv"), newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                delegues.append({
                    "id": int(row["Id"]),
                    "nom": row["Nom"],
                    "level": row["Level"],
                    "score": int(row["Score"])
                })
        return delegues
    except Exception as e:
        print(f"[Erreur] {e}")
        exit(1)


# ─── Sauvegarde session ───────────────────────────────────────────────────

def save_session(delegue, messages):
    os.makedirs("sessions", exist_ok=True)

    filename = f"sessions/{delegue['nom'].replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"

    session = {
        "delegue": delegue,
        "date": datetime.now().isoformat(),
        "conversation": messages
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    print(f"\nSession sauvegardée : {filename}")


# ─── Ollama Streaming ─────────────────────────────────────────────────────

def ask_avatar(messages, lang):
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "gemma:7b",
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            stream=True
        )

        response.raise_for_status()

        full_response = ""
        buffer = ""

        print("\nAvatar : ", end="", flush=True)

        # 🔥 LOCK GLOBAL
        tts_lock.acquire()

        for line in response.iter_lines():
            if not line:
                continue

            chunk = json.loads(line.decode("utf-8"))
            token = chunk.get("message", {}).get("content", "")

            if not token:
                continue

            print(token, end="", flush=True)

            full_response += token
            buffer += token

            if any(p in buffer for p in [".", "!", "?"]):
                speak_text(buffer.strip(), lang)
                buffer = ""
                time.sleep(0.1)

        if buffer.strip():
            speak_text(buffer.strip(), lang)

        print("\n")

        # 🔓 UNLOCK après fin de parole
        tts_lock.release()

        return full_response

    except Exception as e:
        print(f"[Erreur] {e}")
        try:
            tts_lock.release()
        except:
            pass
        return None


# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    delegues = load_delegues()

    print("\n=== Avalive ===\n")
    for d in delegues:
        print(f"{d['id']} - {d['nom']} ({d['level']})")

    try:
        choice = int(input("\nChoisir un délégué : "))
        current_user = next((d for d in delegues if d["id"] == choice), None)

        if not current_user:
            print("Délégué introuvable")
            return

    except:
        print("Entrée invalide")
        return

    print(f"\nSession avec {current_user['nom']}\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(level=current_user["level"])}
    ]

    store = load_or_build_rag()
    retriever = Retriever(store)

    # 🔥 STOCKAGE TRANSCRIPT POUR ÉVALUATION FINALE
    transcript = []

    while True:
        try:
            user_input, lang = speech_to_text()
        except KeyboardInterrupt:
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            break

        # 🔥 CONDITION DE FIN → ÉVALUATION
        if user_input.lower() in ["fin", "end", "finish", "done", "terminé"]:
            print("\n[Evaluation finale]")

            full_text = "\n".join(transcript)

            result = evaluate(full_text)

            if result and result.get("status") != "no_evaluation":
                print("\n=== FINAL EVALUATION ===")
                print(f"Voice Score: {result.get('voice_score')}")
                print(f"Content Score: {result.get('content_score')}")
                print(f"Overall Score: {result.get('overall_score')}")
                print(f"Feedback: {result.get('feedback')}")
            else:
                print("Pas assez d'information pour évaluer.")

            break

        # 🔹 ajouter au transcript
        transcript.append(user_input)

        # 🔹 RAG
        docs = retriever.retrieve(user_input, k=3)
        context = "\n".join(docs)[:1500]

        messages.append({
            "role": "system",
            "content": f"Contexte:\n{context}"
        })

        messages.append({"role": "user", "content": user_input})

        # 🔥 streaming + voix
        reply = ask_avatar(messages, lang)

        if not reply:
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": reply})

    save_session(current_user, messages)
    print("Fin.")


if __name__ == "__main__":
    main()