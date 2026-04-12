"""Semantic search over the persisted VITAL Chroma vector store (read-only)."""

from __future__ import annotations

import os
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR = os.path.join(BASE_DIR, "../../data/clean")
VECTOR_DIR = os.path.join(BASE_DIR, "../../data/vectorstore")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "vital_knowledge"


class VitalRetriever:
    """Query interface for the offline vital_knowledge embedding index."""

    def __init__(self) -> None:
        """Load Chroma collection and embedding model (once per instance)."""
        self._model = SentenceTransformer(MODEL_NAME)
        self._client = chromadb.PersistentClient(path=VECTOR_DIR)
        self._collection: Any = None
        if not os.path.isdir(CLEAN_DIR):
            print(f"Warning: cleaned data folder not found: {CLEAN_DIR}")
        try:
            self._collection = self._client.get_collection(COLLECTION_NAME)
        except Exception:
            self._collection = None
        print("VitalRetriever ready")

    def _encode_query(self, query: str) -> list[float]:
        """Embed a single query string as one vector."""
        emb = self._model.encode(
            [query],
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return emb[0].tolist()

    def _distance_to_score(self, distance: float) -> float:
        """Convert cosine distance to score (1 - distance) for readability."""
        return max(0.0, 1.0 - float(distance))

    def _query_chroma(
        self,
        query: str,
        n_results: int,
        where: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Run a similarity search and return normalized result dicts."""
        try:
            if self._collection is None or self._collection.count() == 0:
                return []
            q_emb = self._encode_query(query.strip())
            if not q_emb:
                return []
            kwargs: dict[str, Any] = {
                "query_embeddings": [q_emb],
                "n_results": min(max(1, n_results), self._collection.count()),
                "include": ["documents", "metadatas", "distances"],
            }
            if where is not None:
                kwargs["where"] = where
            raw = self._collection.query(**kwargs)
            docs = raw.get("documents") or [[]]
            metas = raw.get("metadatas") or [[]]
            dists = raw.get("distances") or [[]]
            row_docs = docs[0] if docs else []
            row_metas = metas[0] if metas else []
            row_dists = dists[0] if dists else []
            out: list[dict[str, Any]] = []
            for text, meta, dist in zip(row_docs, row_metas, row_dists):
                if meta is None:
                    meta = {}
                dval = float(dist) if dist is not None else 1.0
                out.append(
                    {
                        "text": text or "",
                        "metadata": dict(meta) if meta else {},
                        "distance": dval,
                        "score": self._distance_to_score(dval),
                    }
                )
            out.sort(key=lambda x: x["score"], reverse=True)
            return out
        except Exception:
            return []

    def search(
        self,
        query: str,
        n_results: int = 5,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search with optional metadata filter on source."""
        where: dict[str, Any] | None = None
        if source_filter and str(source_filter).strip():
            where = {"source": str(source_filter).strip()}
        return self._query_chroma(query, n_results, where)

    def search_products(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search only vital_products chunks."""
        return self.search(query, n_results=n_results, source_filter="vital_products")

    def search_ingredients(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search only vital_ingredients chunks."""
        return self.search(query, n_results=n_results, source_filter="vital_ingredients")

    def search_guidelines(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search only clinical_guidelines chunks."""
        return self.search(query, n_results=n_results, source_filter="clinical_guidelines")

    def search_warnings(
        self,
        query: str,
        population: str | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search population_warnings with optional exact population metadata filter."""
        where: dict[str, Any]
        if population and str(population).strip():
            where = {
                "$and": [
                    {"source": "population_warnings"},
                    {"population": str(population).strip()},
                ]
            }
        else:
            where = {"source": "population_warnings"}
        return self._query_chroma(query, n_results, where)

    def search_rules(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search only supplement_rules chunks."""
        return self.search(query, n_results=n_results, source_filter="supplement_rules")

    def search_all_sources(
        self,
        query: str,
        n_results_per_source: int = 3,
    ) -> dict[str, list[dict[str, Any]]]:
        """Run one search per major source type for open-ended questions."""
        keys = [
            "vital_products",
            "vital_ingredients",
            "clinical_guidelines",
            "population_warnings",
            "supplement_rules",
        ]
        out: dict[str, list[dict[str, Any]]] = {}
        for k in keys:
            out[k] = self.search(query, n_results=n_results_per_source, source_filter=k)
        return out


if __name__ == "__main__":
    r = VitalRetriever()
    print("\n--- SEMANTIC SEARCH TESTS ---")

    results = r.search_products(
        "produit pour chute de cheveux",
        n_results=3,
    )
    print(f"\nHair loss products ({len(results)} results):")
    for res in results:
        print(
            f"  {res['metadata'].get('product_name', '')} "
            f"(score: {res['score']:.3f})"
        )

    results = r.search_products(
        "complément alimentaire pour enfant avec toux",
        n_results=3,
    )
    print(f"\nChildren cough ({len(results)} results):")
    for res in results:
        print(
            f"  {res['metadata'].get('product_name', '')} "
            f"(score: {res['score']:.3f})"
        )

    results = r.search_warnings(
        "vitamine danger grossesse",
        population="Grossesse",
        n_results=3,
    )
    print(f"\nPregnancy warnings ({len(results)} results):")
    for res in results:
        print(
            f"  {res['metadata'].get('substance', '')} — "
            f"{res['metadata'].get('population', '')}"
        )

    results = r.search_guidelines(
        "hypertension treatment first line",
        n_results=3,
    )
    print(f"\nHypertension guidelines ({len(results)} results):")
    for res in results:
        print(
            f"  {res['metadata'].get('disease_name', '')} — "
            f"{res['metadata'].get('line_of_treatment', '')}"
        )

    all_results = r.search_all_sources(
        "carence en fer femme enceinte",
        n_results_per_source=2,
    )
    print(f"\nAll sources search:")
    for source, items in all_results.items():
        print(f"  {source}: {len(items)} results")

    print("\n--- ALL TESTS PASSED ---")
