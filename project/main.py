import ollama
from agent.prompts import DOCTOR_PROMPT
from rag.rag_build import build_rag
from rag.retriever import Retriever
from utils.voice import speak_text, detect_lang
from utils.speech_to_text import listen_to_user


def ask_model(prompt):
    response = ollama.chat(
        model='llama3.1',
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content']


def simulate(delegate, retriever):
    for i in range(5):
        print("\n Delegate:")
        
        mode = input("Type 't' (text) or 's' (speech): ")

        if mode == "s":
              delegate_input = listen_to_user()
        else:
            delegate_input = input("Ask something: ")

        #  1. détecter langue de la question (IMPORTANT)
        lang = detect_lang(delegate_input)

        #  2. RAG retrieval
        relevant_docs = retriever.retrieve(delegate_input, k=1)
        context = "\n\n".join(relevant_docs)

        print("\n Retrieved context:")
        print(context)
      
        # 3. prompt avec contrainte de langue
        doctor_input = f"""
{DOCTOR_PROMPT}

Relevant product information:
{context}

Delegate level: {delegate.level}

Delegate says:
{delegate_input}

👉 IMPORTANT: Answer in the SAME language as the delegate ({lang}).
"""

        print("\n Doctor:")
        doctor_response = ask_model(doctor_input)

        print(doctor_response)

        # 4. TTS avec la même langue (PAS detect_lang sur réponse )
        speak_text(doctor_response, lang=lang)


if __name__ == "__main__":
    from agent.delegate import Delegate
    from rag.keravel import csv_to_json

    delegate = Delegate(id=1, name="Ines")

    # conversion CSV → JSON
    csv_to_json(
        r"C:\Users\moall\Desktop\dso1\data\keravel_products.csv",
        r"C:\Users\moall\Desktop\dso1\data\keravel_products.json"
    )

    # build RAG
    store = build_rag()
    retriever = Retriever(store)

    # lancer simulation
    simulate(delegate, retriever)