import chromadb
from chromadb.config import Settings

class ChromaStore:
    def __init__(self, collection_name="keravel"):
        self.client = chromadb.Client(Settings(
            persist_directory="./chroma_db"
        ))

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add(self, documents, embeddings):
        for i, doc in enumerate(documents):
            self.collection.add(
                documents=[doc],
                embeddings=[embeddings[i]],
                ids=[str(i)]
            )
        

    def search(self, query_embedding, k=3):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        return results["documents"][0]