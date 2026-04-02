"""Build and persist ChromaDB vector index from cleaned VITAL CSVs (offline embeddings)."""

from __future__ import annotations

import os
import re
import shutil
from typing import Any

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR = os.path.join(BASE_DIR, "../../data/clean")
VECTOR_DIR = os.path.join(BASE_DIR, "../../data/vectorstore")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "vital_knowledge"
BATCH_SIZE = 32
MAX_CHARS = 512


def _clean_text_block(text: Any) -> str:
    """Normalize text before embedding: pipes, whitespace, mojibake, truncate."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text).replace("|", ", ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[?\uFFFD]|â€|â€™|â€œ|â€", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > MAX_CHARS:
        s = s[:MAX_CHARS].rsplit(" ", 1)[0] if " " in s[:MAX_CHARS] else s[:MAX_CHARS]
    return s


def _meta_str(v: Any) -> str:
    """Chroma metadata values must be primitives; store as string."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _combine_parts(*parts: Any) -> str:
    """Join non-empty parts with space."""
    bits = []
    for p in parts:
        t = _clean_text_block(p) if p is not None else ""
        if t:
            bits.append(t)
    return _clean_text_block(" ".join(bits))


def _vectorstore_has_data(path: str) -> bool:
    """Return True if a persisted Chroma store with our collection exists and is non-empty."""
    if not os.path.isdir(path):
        return False
    sqlite = os.path.join(path, "chroma.sqlite3")
    if not os.path.isfile(sqlite):
        return False
    try:
        client = chromadb.PersistentClient(path=path)
        col = client.get_collection(COLLECTION_NAME)
        return col.count() > 0
    except Exception:
        return False


def _load_csv(name: str) -> pd.DataFrame:
    """Load one cleaned CSV from CLEAN_DIR."""
    p = os.path.join(CLEAN_DIR, name)
    return pd.read_csv(p, encoding="utf-8-sig")


def _embed_batches(model: SentenceTransformer, texts: list[str]) -> list[list[float]]:
    """Encode texts in batches of BATCH_SIZE; return list of embedding vectors."""
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        emb = model.encode(batch, batch_size=BATCH_SIZE, show_progress_bar=False, convert_to_numpy=True)
        out.extend(emb.tolist())
    return out


def main() -> None:
    """Build Chroma collection vital_knowledge under VECTOR_DIR."""
    os.makedirs(VECTOR_DIR, exist_ok=True)

    if _vectorstore_has_data(VECTOR_DIR):
        ans = input("Vector store already exists. Rebuild? (y/n): ").strip().lower()
        if ans != "y":
            print("Exiting without rebuild.")
            return
        try:
            shutil.rmtree(VECTOR_DIR)
        except PermissionError as e:
            print(f"PermissionError: {e}. Renaming old vectorstore and creating new.")
            old_dir = VECTOR_DIR + "_old"
            if os.path.exists(old_dir):
                shutil.rmtree(old_dir, ignore_errors=True)
            os.rename(VECTOR_DIR, old_dir)
        os.makedirs(VECTOR_DIR, exist_ok=True)

    print(f"Loading model {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(path=VECTOR_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    counts: dict[str, int] = {
        "vital_products": 0,
        "vital_product_knowledge": 0,
        "vital_ingredients": 0,
        "clinical_guidelines": 0,
        "population_warnings": 0,
        "supplement_rules": 0,
    }

    all_ids: list[str] = []
    all_docs: list[str] = []
    all_meta: list[dict[str, str]] = []

    # vital_products
    df = _load_csv("vital_products_clean.csv")
    print(f"Embedding vital_products: {len(df)} documents...")
    for i, row in df.iterrows():
        text = _combine_parts(
            row.get("name"),
            row.get("categories"),
            row.get("indications"),
            row.get("classe"),
            row.get("forme"),
        )
        if not text:
            continue
        src = "vital_products"
        all_ids.append(f"{src}_{counts[src]}")
        counts[src] += 1
        all_docs.append(text)
        all_meta.append(
            {
                "source": src,
                "product_name": _meta_str(row.get("name")),
                "classe": _meta_str(row.get("classe")),
                "forme": _meta_str(row.get("forme")),
                "url": _meta_str(row.get("url")),
            }
        )

    # vital_product_knowledge
    df = _load_csv("vital_product_knowledge_clean.csv")
    print(f"Embedding vital_product_knowledge: {len(df)} documents...")
    for i, row in df.iterrows():
        text = _combine_parts(
            row.get("nom_produit"),
            row.get("indications"),
            row.get("compositions_brut"),
            row.get("contre_indications_produit"),
            row.get("conseils_d_utilisation"),
        )
        if not text:
            continue
        src = "vital_product_knowledge"
        all_ids.append(f"{src}_{counts[src]}")
        counts[src] += 1
        all_docs.append(text)
        all_meta.append(
            {
                "source": src,
                "product_name": _meta_str(row.get("nom_produit")),
            }
        )

    # vital_ingredients
    df = _load_csv("vital_ingredients_clean.csv")
    print(f"Embedding vital_ingredients: {len(df)} documents...")
    for i, row in df.iterrows():
        text = _combine_parts(
            row.get("ingredient"),
            row.get("role"),
            row.get("synergies"),
            row.get("conflits"),
            row.get("precautions"),
        )
        if not text:
            continue
        src = "vital_ingredients"
        all_ids.append(f"{src}_{counts[src]}")
        counts[src] += 1
        all_docs.append(text)
        all_meta.append(
            {
                "source": src,
                "ingredient_name": _meta_str(row.get("ingredient")),
            }
        )

    # clinical_guidelines
    df = _load_csv("clinical_guidelines_clean.csv")
    print(f"Embedding clinical_guidelines: {len(df)} documents...")
    for i, row in df.iterrows():
        text = _combine_parts(
            row.get("disease_name"),
            row.get("recommended_drug_class"),
            row.get("decision_factors"),
            row.get("contraindications_summary"),
        )
        if not text:
            continue
        src = "clinical_guidelines"
        all_ids.append(f"{src}_{counts[src]}")
        counts[src] += 1
        all_docs.append(text)
        all_meta.append(
            {
                "source": src,
                "disease_name": _meta_str(row.get("disease_name")),
                "line_of_treatment": _meta_str(row.get("line_of_treatment")),
            }
        )

    # population_warnings
    df = _load_csv("population_warnings_clean.csv")
    print(f"Embedding population_warnings: {len(df)} documents...")
    for i, row in df.iterrows():
        text = _combine_parts(
            row.get("substance"),
            row.get("population_condition"),
            row.get("type_alerte"),
            row.get("explication_detaillee"),
            row.get("conduite_a_tenir"),
        )
        if not text:
            continue
        src = "population_warnings"
        all_ids.append(f"{src}_{counts[src]}")
        counts[src] += 1
        all_docs.append(text)
        all_meta.append(
            {
                "source": src,
                "substance": _meta_str(row.get("substance")),
                "population": _meta_str(row.get("population_condition")),
                "severite": _meta_str(row.get("severite")),
            }
        )

    # supplement_rules
    df = _load_csv("supplement_rules_clean.csv")
    print(f"Embedding supplement_rules: {len(df)} documents...")
    for i, row in df.iterrows():
        text = _combine_parts(
            row.get("substance_sujet"),
            row.get("regle"),
            row.get("explication_detaillee"),
            row.get("conduite_a_tenir"),
        )
        if not text:
            continue
        src = "supplement_rules"
        all_ids.append(f"{src}_{counts[src]}")
        counts[src] += 1
        all_docs.append(text)
        all_meta.append(
            {
                "source": src,
                "substance": _meta_str(row.get("substance_sujet")),
                "importance": _meta_str(row.get("importance")),
            }
        )

    if not all_ids:
        print("No documents to embed. Exiting.")
        return

    embeddings = _embed_batches(model, all_docs)
    for i in range(0, len(all_ids), BATCH_SIZE):
        collection.add(
            ids=all_ids[i : i + BATCH_SIZE],
            embeddings=embeddings[i : i + BATCH_SIZE],
            documents=all_docs[i : i + BATCH_SIZE],
            metadatas=all_meta[i : i + BATCH_SIZE],
        )

    total = sum(counts.values())
    print("Vector store built:")
    print(f"  vital_products:          {counts['vital_products']} documents")
    print(f"  vital_product_knowledge: {counts['vital_product_knowledge']} documents")
    print(f"  vital_ingredients:       {counts['vital_ingredients']} documents")
    print(f"  clinical_guidelines:     {counts['clinical_guidelines']} documents")
    print(f"  population_warnings:     {counts['population_warnings']} documents")
    print(f"  supplement_rules:        {counts['supplement_rules']} documents")
    print(f"  TOTAL:                   {total} documents")


if __name__ == "__main__":
    main()
