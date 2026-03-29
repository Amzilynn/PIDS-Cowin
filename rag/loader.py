import json


def load_json(json_path):
    """
    Charge le fichier JSON et retourne une liste de produits
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def product_to_text(item):
    """
    Transforme un produit en texte structuré pour le RAG
    """
    return f"""
Product: {item.get('product', '')}

Description:
{item.get('description', '')}

Ingredients:
{item.get('ingredients', '')}

Advice:
{item.get('advice', '')}

Storage:
{item.get('storage', '')}
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