# rag/rag_build.py
from rag.data import csv_to_json
from rag.loader import load_json, build_documents
from rag.chunk import chunk_by_product
from rag.embedder import embed
from rag.vector_store import ChromaStore
import os

def build_rag():
    # créer JSON à partir du CSV si nécessaire
    if not os.path.exists("C:/Users/moall/Desktop/dso1/data/vital_products.json"):
        csv_to_json()

    data = load_json("C:/Users/moall/Desktop/dso1/data/vital_products.json")
    documents = build_documents(data)
    chunks = chunk_by_product(documents)

    embeddings = [embed(chunk) for chunk in chunks]

    store = ChromaStore()
    store.add(chunks, embeddings)

    print(f"RAG prêt ✅ - {len(chunks)} chunks ajoutés")
    return store



def load_or_build_rag():
    if os.path.exists("../chroma_db"):
        print("Rechargement de Chroma depuis le disque…")
        store = ChromaStore()
    else:
        print("Construction du RAG…")
        store = build_rag()
    return store