import requests
import csv
import json
import os
from datetime import datetime
from Agent.prompts import SYSTEM_PROMPT
from Agent.voice import speak_text
from Agent.stt import speech_to_text

from rag.rag_build import load_or_build_rag
from rag.retriever import Retriever

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
    except FileNotFoundError:
        print("[Erreur] Le fichier delegues.csv est introuvable.")
        exit(1)
    except Exception as e:
        print(f"[Erreur] Impossible de lire les délégués : {e}")
        exit(1)


# ─── Sauvegarde de session ─────────────────────────────────────────────────

def save_session(delegue, messages):
    try:
        os.makedirs("sessions", exist_ok=True)

        session = {
            "delegue": {
                "id": delegue["id"],
                "nom": delegue["nom"],
                "level": delegue["level"],
                "score": delegue["score"]
            },
            "date": datetime.now().isoformat(),
            "conversation": messages,
            "evaluation": None  # sera rempli plus tard par le moteur d'évaluation
        }

        nom_fichier = delegue["nom"].replace(" ", "_")
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"sessions/{nom_fichier}_{date_str}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        print(f"\n Session sauvegardée : {filename}")

    except Exception as e:
        print(f"[Erreur] Impossible de sauvegarder la session : {e}")


# ─── Appel à Ollama ────────────────────────────────────────────────────────

def ask_avatar(messages):
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    except requests.exceptions.ConnectionError:
        print("[Erreur] Ollama n'est pas lancé. Démarre-le avec : ollama serve")
        return None
    except requests.exceptions.Timeout:
        print("[Erreur] Ollama met trop de temps à répondre.")
        return None
    except Exception as e:
        print(f"[Erreur] Problème avec Ollama : {e}")
        return None


# ─── Programme principal ───────────────────────────────────────────────────

def main():
    delegues = load_delegues()

    print("\n=== Avalive — Sélection du délégué ===\n")
    for d in delegues:
        print(f"  {d['id']} - {d['nom']} ({d['level']})")

    try:
        choice = int(input("\nChoisir un délégué (numéro) : "))
        current_user = next((d for d in delegues if d["id"] == choice), None)
        if current_user is None:
            print("[Erreur] Délégué introuvable.")
            return
    except ValueError:
        print("[Erreur] Entre un numéro valide.")
        return

    level = current_user["level"]
    print(f"\nSession démarrée avec {current_user['nom']} — niveau {level}\n")
    print("(Tape 'exit' ou 'quit' pour terminer la session)\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(level=level)}
    ]
    store = load_or_build_rag()
    retriever = Retriever(store)
    
    while True:
        try:
            user_input, lang = speech_to_text()
        except KeyboardInterrupt:
            print("\n\nSession interrompue.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            break


        

             # 🔹 1️⃣ Recherche RAG
        relevant_docs = retriever.retrieve(user_input, k=3)
        context_text = "\n".join(relevant_docs)

       # 🔹 2️⃣ Ajouter le contexte au prompt
        messages.append({"role": "system", "content": f"Voici des informations sur les produits Vital :\n{context_text}"})
        # Ajouter le message de l'utilisateur
        messages.append({"role": "user", "content": user_input})
        avatar_reply = ask_avatar(messages)

        if avatar_reply is None:
            messages.pop()  # annule le message si pas de réponse
            continue

        print(f"\nAvatar : {avatar_reply}\n")
        speak_text(avatar_reply, lang)

        messages.append({"role": "assistant", "content": avatar_reply})

    save_session(current_user, messages)
    print("À bientôt !")


if __name__ == "__main__":
    main()