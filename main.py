print("START")

try:
    print("IMPORTS...")
    import requests
    import csv
    import json
    import os
    from datetime import datetime
    from groq import Groq
    from dotenv import load_dotenv
    print("IMPORT OK")
except Exception as e:
    print("ERROR:", e)
    exit()

from Agent.prompts import SYSTEM_PROMPT
from Agent.voice import speak_text, is_speaking
from Agent.stt import speech_to_text

from rag.rag_build import load_or_build_rag
from rag.retriever import Retriever



load_dotenv()
print(os.getenv("GROQ_API_KEY"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
 
GROQ_MODEL = "llama-3.3-70b-versatile"

print("START")

# ─── Mots-clés qui déclenchent la recherche RAG ───────────────────────────────
# Le RAG n'est activé QUE si le délégué parle d'un produit
PRODUCT_TRIGGER_KEYWORDS = [
    "produit", "product", "médicament", "medicine", "drug",
    "présenter", "present", "proposer", "propose",
    "comprimé", "capsule", "sirop", "complément",
    "indication", "posologie", "dosage", "traitement", "effet",
    "principe actif", "composition", "contre-indication",
]
def should_use_rag(text: str) -> bool:
    """Retourne True seulement si le délégué parle d'un produit."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PRODUCT_TRIGGER_KEYWORDS)

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


# ─── Appel à Groq ────────────────────────────────────────────────────────

def ask_avatar(messages: list) -> str | None:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=120,        # réponses courtes = plus naturel
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Erreur Groq] {e}")
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
            # 🔴 attendre que l’avatar finisse de parler
            while is_speaking:
                continue

            user_input, lang = speech_to_text()
        except KeyboardInterrupt:
            print("\n\nSession interrompue.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            break


        

        print(f"\n🗣️  Délégué : {user_input}")
 
        # ── RAG conditionnel : uniquement si le délégué parle d'un produit ──
        messages_to_send = list(messages)  # copie pour ne pas polluer l'historique
 
        if should_use_rag(user_input):
            relevant_docs = retriever.retrieve(user_input, k=3)  # k=2 suffit
            if relevant_docs:
                context_text = "\n".join(relevant_docs)
                # Injecté comme message système temporaire, pas stocké dans l'historique
                messages_to_send.append({
                    "role": "system",
                    "content": (
                        "CONTEXTE PRODUIT (Use this context ONLY if the delegate is clearly talking about this product. Otherwise ignore it.) :\n" + context_text
                    )
                })
 
        # Ajouter le message de l'utilisateur
        messages_to_send.append({"role": "user", "content": user_input})
 
        avatar_reply = ask_avatar(messages_to_send)
 
        if avatar_reply is None:
            print("[⚠️] Pas de réponse, réessaie.")
            continue
 
        print(f"\n🤖 Avatar : {avatar_reply}\n")
        speak_text(avatar_reply, lang)
 
        # Stocker dans l'historique réel (sans le contexte RAG temporaire)
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": avatar_reply})

    save_session(current_user, messages)
    print("À bientôt !")


if __name__ == "__main__":
    main()