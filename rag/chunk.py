# rag/chunk.py

def chunk_by_product(documents):
    """
    Chaque produit devient un chunk unique
    (1 document = 1 chunk)

    Parameters:
        documents (list[str]): liste de textes produits par le loader

    Returns:
        list[str]: liste de chunks
    """
    chunks = []

    for doc in documents:
        clean_doc = doc.strip()
        if clean_doc:  # éviter les textes vides
            chunks.append(clean_doc)

    return chunks