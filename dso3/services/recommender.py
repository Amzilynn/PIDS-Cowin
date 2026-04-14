import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dso3.services.embedding import get_embedding, cosine

def recommend_delegates(product, delegates):
    product_text = f"{product.category} {product.description}"
    product_vec = get_embedding(product_text)

    results = []

    for delegate in delegates:
        delegate_text = f"{delegate.expertise} {delegate.interests}"
        delegate_vec = get_embedding(delegate_text)

        score = cosine(product_vec, delegate_vec)

        if score < 0.35:
            continue

        results.append({
            "delegate_id": delegate.id,
            "delegate_name": delegate.name,
            "score": float(score)
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:5]