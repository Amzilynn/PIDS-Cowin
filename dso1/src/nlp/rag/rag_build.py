# rag/rag_build.py
from .data import csv_to_json
from .loader import load_json, build_documents
from .chunk import chunk_by_product
from .embedder import embed
from .vector_store import ChromaStore
import os
from pathlib import Path

# Chemins relatifs à dso1 (ancêtre de nlp/rag)
# __file__ est dso1/src/nlp/rag/rag_build.py
# parent = dso1/src/nlp/rag/
# parent.parent = dso1/src/nlp/
# parent.parent.parent = dso1/src/
# parent.parent.parent.parent = dso1/
DSO1_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = DSO1_ROOT / "Data"
CHROMA_DB_PATH = DSO1_ROOT / "chroma_db"

def build_rag():
    # créer JSON à partir du CSV si nécessaire
    json_path = DATA_DIR / "vital_products.json"
    if not json_path.exists():
        csv_to_json()

    data = load_json(str(json_path))
    documents = build_documents(data)
    chunks = chunk_by_product(documents)

    embeddings = [embed(chunk) for chunk in chunks]

    store = ChromaStore()
    store.add(chunks, embeddings)

    print(f"RAG prêt ✅ - {len(chunks)} chunks ajoutés")
    return store



def load_or_build_rag():
    if CHROMA_DB_PATH.exists():
        print("Rechargement de Chroma depuis le disque…")
        store = ChromaStore()
    else:
        print("Construction du RAG…")
        store = build_rag()
    return store