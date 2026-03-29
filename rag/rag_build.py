from rag.loader import load_json, build_documents
from rag.chunk import chunk_by_product
from rag.embedder import embed
from rag.vector_store import ChromaStore


def build_rag():
    data = load_json(r"C:\Users\moall\Desktop\dso1\data\keravel_products.json")

    documents = build_documents(data)
    chunks = chunk_by_product(documents)
    

    embeddings = [embed(chunk) for chunk in chunks]

    store = ChromaStore()
    store.add(chunks, embeddings)
   

    return store