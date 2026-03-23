from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import json
import pickle

from sklearn.metrics.pairwise import cosine_similarity


def retrieve(index_dir: Path, question: str, top_k: int = 4) -> List[Dict[str, str]]:
    chunks_path = index_dir / "chunks.json"
    vectorizer_path = index_dir / "vectorizer.pkl"
    tfidf_path = index_dir / "tfidf.pkl"

    if not chunks_path.exists() or not vectorizer_path.exists() or not tfidf_path.exists():
        raise FileNotFoundError(
            "Index introuvable. Lance d'abord l'ingestion pour créer l'index RAG."
        )

    with chunks_path.open("r", encoding="utf-8") as file:
        chunks: List[Dict[str, str]] = json.load(file)

    with vectorizer_path.open("rb") as file:
        vectorizer = pickle.load(file)

    with tfidf_path.open("rb") as file:
        matrix = pickle.load(file)

    question_vec = vectorizer.transform([question])
    scores = cosine_similarity(question_vec, matrix).flatten()
    ranked_indices = scores.argsort()[::-1][:top_k]

    retrieved: List[Dict[str, str]] = []
    for idx in ranked_indices:
        chunk = chunks[idx]
        retrieved.append(
            {
                "id": chunk["id"],
                "source": chunk["source"],
                "text": chunk["text"],
                "score": float(scores[idx]),
            }
        )

    return retrieved