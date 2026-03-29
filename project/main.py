import ollama
from agent.prompts import DOCTOR_PROMPT
from rag.rag_build import build_rag
from rag.chunk import chunk_by_product
from rag.retriever import Retriever

def ask_model(prompt):
    response = ollama.chat(
        model='llama3.1',
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content']


def simulate(delegate,retriever):
    for i in range(5):
        print("\n Delegate:")
        delegate_input = input("Ask something: ")

        # RAG retrieval
        relevant_docs = retriever.retrieve(delegate_input, k=1)

        context = "\n\n".join(relevant_docs)
        print(context)

        doctor_input = f"""
{DOCTOR_PROMPT}

Relevant product information:
{context}

Delegate level: {delegate.level}

Delegate says:
{delegate_input}
"""

        print("\n Doctor:")
        doctor_response = ask_model(doctor_input)
        print(doctor_response)


if __name__ == "__main__":
    from agent.delegate import Delegate

    delegate = Delegate(id=1, name="Ines")
    from rag.keravel import csv_to_json

    csv_to_json(
    r"C:\Users\moall\Desktop\dso1\data\keravel_products.csv",
    r"C:\Users\moall\Desktop\dso1\data\keravel_products.json"
)
    store=build_rag()
    retriever = Retriever(store)
    simulate(delegate, retriever)
   
    
