from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import ProductRecord, RetrievedChunk


@dataclass(frozen=True)
class IndexStats:
    product_count: int
    chunk_count: int


class ProductRAG:
    """Student-friendly RAG retriever using TF-IDF + cosine similarity."""

    def __init__(self, products: List[ProductRecord]) -> None:
        self._products = products
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        self._chunks: List[str] = []
        self._chunk_meta: List[dict] = []
        self._matrix = None
        self.reindex()

    def stats(self) -> IndexStats:
        return IndexStats(product_count=len(self._products), chunk_count=len(self._chunks))

    def reindex(self) -> IndexStats:
        self._chunks = []
        self._chunk_meta = []

        for i, product in enumerate(self._products, start=1):
            text = _product_to_text(product)
            self._chunks.append(text)
            self._chunk_meta.append(
                {
                    "chunk_id": f"product_{i}",
                    "product_name": product.name,
                    "url": product.url,
                    "class": product.product_class,
                    "form": product.form,
                }
            )

        if self._chunks:
            self._matrix = self._vectorizer.fit_transform(self._chunks)
        else:
            self._matrix = None

        return self.stats()

    def retrieve(self, question: str, top_k: int = 5) -> List[RetrievedChunk]:
        query = question.strip()
        if not query:
            raise ValueError("Question must not be empty.")
        if self._matrix is None or not self._chunks:
            return []

        top_k = max(1, min(top_k, len(self._chunks)))

        expanded_query = _expand_query(query)
        query_vec = self._vectorizer.transform([expanded_query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        top_idx = scores.argsort()[::-1][:top_k]

        results: List[RetrievedChunk] = []
        for idx in top_idx:
            meta = self._chunk_meta[idx]
            results.append(
                RetrievedChunk(
                    chunk_id=meta["chunk_id"],
                    product_name=meta["product_name"],
                    score=float(scores[idx]),
                    text=self._chunks[idx],
                    metadata={
                        "url": meta["url"],
                        "class": meta["class"],
                        "form": meta["form"],
                    },
                )
            )
        return results


def _product_to_text(product: ProductRecord) -> str:
    categories = ", ".join(product.categories)
    parts = [
        f"Product: {product.name}",
        f"Class: {product.product_class}",
        f"Form: {product.form}",
        f"Categories: {categories}",
        f"Indications: {product.indications}",
        f"Composition: {product.composition}",
        f"Usage advice: {product.usage_advice}",
        f"Contraindications: {product.contraindications}",
    ]
    text = " | ".join(part for part in parts if not part.endswith(": "))
    return _normalize_text(text)


def _normalize_text(text: str) -> str:
    no_accents = "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )
    no_accents = no_accents.lower()
    no_accents = re.sub(r"[^a-z0-9\s]", " ", no_accents)
    return " ".join(no_accents.split())


def _expand_query(query: str) -> str:
    q = _normalize_text(query)
    synonyms = {
        "dry cough": "dry cough toux seche toux",
        "wet cough": "wet cough toux grasse toux",
        "cough": "cough toux",
        "immunity": "immunity immunite defense",
        "pregnancy": "pregnancy grossesse",
        "anemia": "anemia anemie fer",
        "hair loss": "hair loss anti chute cheveux",
    }
    for key, value in synonyms.items():
        if key in q:
            q = f"{q} {value}"
    return q
