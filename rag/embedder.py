# rag/embedder.py
from sentence_transformers import SentenceTransformer

# modèle léger et efficace
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed(text):
    """
    Retourne l'embedding du texte sous forme de liste
    """
    return model.encode(text).tolist()