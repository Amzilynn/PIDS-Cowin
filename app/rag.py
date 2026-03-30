from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import math
import os
import re
import json
from collections import Counter
import unicodedata

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ0-9]{2,}", (text or "").lower())


def _normalize_text(text: str) -> str:
    clean = unicodedata.normalize("NFKD", text or "")
    clean = "".join(char for char in clean if not unicodedata.combining(char))
    clean = clean.lower()
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


_DOSAGE_PATTERN = re.compile(
    r"\b\d+(?:[\.,]\d+)?\s?(?:mg|g|mcg|µg|ug|ml|%|ui)(?:\s*/\s*\d+(?:[\.,]\d+)?\s?(?:mg|g|mcg|µg|ug|ml|%|ui))?\b",
    re.IGNORECASE,
)
_PACK_PATTERN = re.compile(
    r"\b(?:bo[iî]te|bte|tube|flacon|ampoule|sachet|sachets|ovule|ovules|suppositoire|suppositoires)\s*(?:de)?\s*\d+(?:[\.,]\d+)?(?:\s?(?:cp|gelules?|ml|mg|g|doses?))?\b",
    re.IGNORECASE,
)


def _extract_query_features(text: str) -> Dict[str, str]:
    normalized = _normalize_text(text)
    dosage_match = _DOSAGE_PATTERN.search(normalized)
    pack_match = _PACK_PATTERN.search(normalized)
    return {
        "normalized": normalized,
        "dosage": dosage_match.group(0).strip() if dosage_match else "",
        "pack": pack_match.group(0).strip() if pack_match else "",
    }


def _extract_doc_features(text: str) -> Dict[str, str]:
    normalized = _normalize_text(text)

    base_match = re.search(r"\[produit_base\]\s*([^\|\n]+)", normalized)
    dosage_match = re.search(r"\[dosage_variante\]\s*([^\|\n]+)", normalized)
    pack_match = re.search(r"\[pack_variante\]\s*([^\|\n]+)", normalized)

    fallback_dosage = _DOSAGE_PATTERN.search(normalized)
    fallback_pack = _PACK_PATTERN.search(normalized)

    return {
        "normalized": normalized,
        "product_base": base_match.group(1).strip() if base_match else "",
        "dosage": dosage_match.group(1).strip() if dosage_match else (fallback_dosage.group(0).strip() if fallback_dosage else ""),
        "pack": pack_match.group(1).strip() if pack_match else (fallback_pack.group(0).strip() if fallback_pack else ""),
    }


def _product_variant_adjustment(question: str, document: str) -> float:
    query_features = _extract_query_features(question)
    doc_features = _extract_doc_features(document)

    adjustment = 0.0
    normalized_query = query_features["normalized"]
    product_base = doc_features["product_base"]

    if product_base:
        base_tokens = [token for token in re.findall(r"[a-z0-9]{3,}", product_base) if token not in {"boite", "tube", "flacon"}]
        if base_tokens and all(token in normalized_query for token in base_tokens[:2]):
            adjustment += 0.08

    query_dosage = query_features["dosage"]
    doc_dosage = doc_features["dosage"]
    if query_dosage and doc_dosage:
        if query_dosage == doc_dosage:
            adjustment += 0.18
        elif query_dosage not in doc_features["normalized"]:
            adjustment -= 0.10

    query_pack = query_features["pack"]
    doc_pack = doc_features["pack"]
    if query_pack and doc_pack:
        if query_pack == doc_pack:
            adjustment += 0.14
        elif query_pack not in doc_features["normalized"]:
            adjustment -= 0.08

    return adjustment


def _lexical_score(question: str, document: str) -> float:
    query_tokens = _tokenize(question)
    doc_tokens = _tokenize(document)
    if not query_tokens or not doc_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    covered = 0
    total = sum(query_counts.values())
    for token, count in query_counts.items():
        covered += min(count, doc_counts.get(token, 0))

    return max(0.0, min(1.0, covered / max(1, total)))


def _rerank_candidates(
    *,
    question: str,
    base_candidates: List[Dict[str, object]],
    top_k: int,
    alpha_semantic: float,
    alpha_lexical: float,
    min_score: float,
    max_per_source: int,
) -> List[Dict[str, str]]:
    alpha_semantic = max(0.0, min(1.0, float(alpha_semantic)))
    alpha_lexical = max(0.0, min(1.0, float(alpha_lexical)))
    alpha_total = alpha_semantic + alpha_lexical
    if alpha_total <= 0:
        alpha_semantic, alpha_lexical = 0.7, 0.3
        alpha_total = 1.0
    alpha_semantic /= alpha_total
    alpha_lexical /= alpha_total

    candidates: List[Dict[str, object]] = []
    for candidate in base_candidates:
        semantic_score = max(0.0, min(1.0, float(candidate.get("semantic_score", 0.0))))
        document_text = str(candidate.get("text", ""))
        lexical = _lexical_score(question, document_text)
        combined_score = (alpha_semantic * semantic_score) + (alpha_lexical * lexical)
        combined_score += _product_variant_adjustment(question, document_text)
        combined_score = max(0.0, min(1.0, combined_score))

        candidates.append(
            {
                "id": str(candidate.get("id", "unknown")),
                "source": str(candidate.get("source", "unknown")),
                "text": document_text,
                "score": combined_score,
            }
        )

    candidates.sort(key=lambda item: float(item["score"]), reverse=True)

    retrieved: List[Dict[str, str]] = []
    per_source_counter: Dict[str, int] = {}
    for candidate in candidates:
        source = str(candidate["source"])
        if float(candidate["score"]) < float(min_score):
            continue
        if per_source_counter.get(source, 0) >= max(1, max_per_source):
            continue
        per_source_counter[source] = per_source_counter.get(source, 0) + 1

        retrieved.append(
            {
                "id": str(candidate["id"]),
                "source": source,
                "text": str(candidate["text"]),
                "score": float(candidate["score"]),
            }
        )
        if len(retrieved) >= max(1, top_k):
            break

    return retrieved


def _retrieve_from_chunks_json(
    *,
    index_dir: Path,
    question: str,
    top_k: int,
    fetch_k: int,
    alpha_semantic: float,
    alpha_lexical: float,
    min_score: float,
    max_per_source: int,
) -> List[Dict[str, str]]:
    chunks_path = index_dir / "chunks.json"
    if not chunks_path.exists():
        return []

    try:
        with chunks_path.open("r", encoding="utf-8") as file:
            chunks: List[Dict[str, object]] = json.load(file)
    except Exception:
        return []

    lexical_ranked = sorted(
        chunks,
        key=lambda chunk: _lexical_score(question, str(chunk.get("text", ""))),
        reverse=True,
    )
    lexical_ranked = lexical_ranked[: max(1, fetch_k)]

    base_candidates: List[Dict[str, object]] = []
    for item in lexical_ranked:
        base_candidates.append(
            {
                "id": str(item.get("id", "unknown")),
                "source": str(item.get("source", "unknown")),
                "text": str(item.get("text", "")),
                "semantic_score": float(_lexical_score(question, str(item.get("text", "")))),
            }
        )

    return _rerank_candidates(
        question=question,
        base_candidates=base_candidates,
        top_k=top_k,
        alpha_semantic=alpha_semantic,
        alpha_lexical=alpha_lexical,
        min_score=min_score,
        max_per_source=max_per_source,
    )


def retrieve(
    index_dir: Path,
    question: str,
    top_k: int = 4,
    collection_name: str = "medical_docs",
    embedding_model: str = "default",
    fetch_k: int = 24,
    alpha_semantic: float = 0.72,
    alpha_lexical: float = 0.28,
    min_score: float = 0.16,
    max_per_source: int = 3,
) -> List[Dict[str, str]]:
    if not index_dir.exists():
        raise FileNotFoundError(
            "Index introuvable. Lance d'abord l'ingestion pour créer l'index RAG."
        )

    try:
        if embedding_model.strip().lower() == "default":
            embedding_function = embedding_functions.ONNXMiniLM_L6_V2()
        else:
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model,
            )

        os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")
        client = chromadb.PersistentClient(
            path=str(index_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

        result = collection.query(
            query_texts=[question],
            n_results=max(top_k, fetch_k, 1),
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        base_candidates: List[Dict[str, object]] = []
        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 1.0
            semantic_score = max(0.0, min(1.0, 1.0 - float(distance if not math.isnan(distance) else 1.0)))

            base_candidates.append(
                {
                    "id": str(metadata.get("id", f"chunk_{index}")),
                    "source": str(metadata.get("source", "unknown")),
                    "text": str(document),
                    "semantic_score": semantic_score,
                }
            )

        return _rerank_candidates(
            question=question,
            base_candidates=base_candidates,
            top_k=top_k,
            alpha_semantic=alpha_semantic,
            alpha_lexical=alpha_lexical,
            min_score=min_score,
            max_per_source=max_per_source,
        )
    except Exception:
        return _retrieve_from_chunks_json(
            index_dir=index_dir,
            question=question,
            top_k=top_k,
            fetch_k=fetch_k,
            alpha_semantic=alpha_semantic,
            alpha_lexical=alpha_lexical,
            min_score=min_score,
            max_per_source=max_per_source,
        )