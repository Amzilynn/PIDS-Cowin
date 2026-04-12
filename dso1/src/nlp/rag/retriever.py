# rag/retriever.py
from .embedder import embed

class Retriever:
    def __init__(self, store):
        self.store = store

    def retrieve(self, query, k=3):
        query_embedding = embed(query)
        return self.store.search(query_embedding, k)