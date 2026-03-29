from sentence_transformers import SentenceTransformer

# modèle léger et efficace
model = SentenceTransformer('all-MiniLM-L6-v2')


def embed(text):
    return model.encode(text).tolist()