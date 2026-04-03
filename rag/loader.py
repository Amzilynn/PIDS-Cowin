# rag/loader.py
import json

def load_json(json_path):
    """
    Charge le fichier JSON et retourne une liste de produits
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def product_to_text(item):
    """
    Transforme un produit en texte structuré pour le RAG
    """
    return f"""
Nom: {item.get('name', '')}
Catégories: {item.get('categories', '')}
Forme: {item.get('forme', '')}
Indications: {item.get('indications', '')}
Classe: {item.get('classe', '')}
Compositions: {item.get('compositions', '')}
Conseils: {item.get('conseils', '')}
Contre-indications: {item.get('contre_indications', '')}
Infos supplémentaires: {item.get('infos_sur_le_produit', '')}
URL: {item.get('url', '')}
Image: {item.get('image', '')}
"""

def build_documents(data):
    """
    Convertit toute la base JSON en documents texte
    """
    documents = []
    for item in data:
        text = product_to_text(item)
        documents.append(text.strip())
    return documents