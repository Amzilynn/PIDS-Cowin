from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import json
import re
import csv
import os
import shutil
import chardet
import unicodedata

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from pypdf import PdfReader


_COLUMN_MAPPINGS_CACHE: Dict[str, object] | None = None


def _read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    texts: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            texts.append(text)
    return "\n".join(texts)


def _read_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _detect_encoding(file_path: Path) -> str:
    with file_path.open("rb") as file:
        raw = file.read(10000)
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8") or "utf-8"


def _detect_separator(file_path: Path, encoding: str) -> str:
    sample_lines: List[str] = []
    with file_path.open("r", encoding=encoding, errors="replace", newline="") as file:
        for _ in range(5):
            line = file.readline()
            if not line:
                break
            sample_lines.append(line)
    sample = "".join(sample_lines)
    return ";" if sample.count(";") > sample.count(",") else ","


def _is_valid_cell(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    return text.lower() not in {"nan", "none", "null"}


def _normalize_colname(name: str) -> str:
    clean = (name or "").strip().replace("�", "")
    clean = unicodedata.normalize("NFKD", clean)
    clean = clean.encode("ascii", "ignore").decode("ascii")
    clean = clean.lower()
    clean = re.sub(r"[^a-z0-9]+", "_", clean)
    return clean.strip("_")


def _default_column_mappings() -> Dict[str, object]:
    return {
        "default": {
            "priority_columns": {
                "nom": "PRODUIT",
                "dci": "DCI",
                "dosage": "DOSAGE",
                "forme": "FORME",
                "indications": "INDICATION",
                "classe": "CLASSE",
                "sous_classe": "SOUS_CLASSE",
                "laboratoire": "LABORATOIRE",
                "statut_amm": "STATUT",
                "presentation": "PRESENTATION",
                "conditionnement_primaire": "CONDITIONNEMENT_PRIMAIRE",
                "spec_conditionnement": "SPEC_CONDITIONNEMENT",
                "amm": "AMM",
                "date_amm": "DATE_AMM",
                "product": "PRODUIT",
                "description": "DESCRIPTION",
                "categories": "CATEGORIES",
            },
            "focus_columns": [],
            "include_other_columns": True,
        },
        "sources": {},
    }


def _normalize_mapping_cfg(cfg: Dict[str, object]) -> Dict[str, object]:
    normalized = dict(cfg)
    priority = cfg.get("priority_columns", {}) if isinstance(cfg, dict) else {}
    if isinstance(priority, dict):
        normalized["priority_columns"] = {
            _normalize_colname(str(key)): str(value)
            for key, value in priority.items()
        }
    focus = cfg.get("focus_columns", []) if isinstance(cfg, dict) else []
    if isinstance(focus, list):
        normalized["focus_columns"] = [_normalize_colname(str(item)) for item in focus]
    normalized["include_other_columns"] = bool(cfg.get("include_other_columns", True)) if isinstance(cfg, dict) else True
    return normalized


def _load_column_mappings() -> Dict[str, object]:
    global _COLUMN_MAPPINGS_CACHE
    if _COLUMN_MAPPINGS_CACHE is not None:
        return _COLUMN_MAPPINGS_CACHE

    config = _default_column_mappings()
    mapping_path = Path(__file__).with_name("column_mappings.json")
    if mapping_path.exists():
        try:
            user_cfg = json.loads(mapping_path.read_text(encoding="utf-8"))
            if isinstance(user_cfg, dict):
                user_default = user_cfg.get("default", {})
                if isinstance(user_default, dict):
                    config["default"] = {
                        **config["default"],
                        **_normalize_mapping_cfg(user_default),
                    }

                user_sources = user_cfg.get("sources", {})
                if isinstance(user_sources, dict):
                    normalized_sources: Dict[str, object] = {}
                    for file_name, source_cfg in user_sources.items():
                        if isinstance(source_cfg, dict):
                            normalized_sources[str(file_name).lower()] = _normalize_mapping_cfg(source_cfg)
                    config["sources"] = normalized_sources
        except Exception:
            pass

    _COLUMN_MAPPINGS_CACHE = config
    return config


def _resolve_source_mapping(file_path: Path) -> Dict[str, object]:
    mappings = _load_column_mappings()
    default_cfg = mappings.get("default", {}) if isinstance(mappings, dict) else {}
    sources_cfg = mappings.get("sources", {}) if isinstance(mappings, dict) else {}

    source_cfg: Dict[str, object] = {}
    if isinstance(sources_cfg, dict):
        source_cfg = sources_cfg.get(file_path.name.lower(), {})
        if not isinstance(source_cfg, dict):
            source_cfg = {}

    resolved = dict(default_cfg) if isinstance(default_cfg, dict) else {}
    resolved.update(source_cfg)

    resolved["priority_columns"] = resolved.get("priority_columns", {}) if isinstance(resolved.get("priority_columns", {}), dict) else {}
    resolved["focus_columns"] = resolved.get("focus_columns", []) if isinstance(resolved.get("focus_columns", []), list) else []
    resolved["include_other_columns"] = bool(resolved.get("include_other_columns", True))
    return resolved


def _detect_medical_columns(fieldnames: List[str]) -> Dict[str, List[str]]:
    """Detect medical priority columns (indication, dosage, contraindication, etc)."""
    medical_keywords = {
        "indication": ["indication", "use", "efficacy", "utilisation"],
        "posology": ["posology", "dosage", "dose", "dosing", "posologie"],
        "contraindication": ["contraindication", "ci", "contre-indication"],
        "side_effect": ["side effect", "adverse", "effet secondaire", "adr"],
        "composition": ["composition", "ingredients", "actif", "substance"],
        "product": ["product", "produit", "name", "nom"],
    }
    detected = {key: [] for key in medical_keywords}
    for field in fieldnames:
        field_lower = _normalize_colname(field)
        for category, keywords in medical_keywords.items():
            if any(keyword in field_lower for keyword in keywords):
                detected[category].append(field)
                break
    return detected


def _read_csv_rows(file_path: Path) -> List[str]:
    encoding = _detect_encoding(file_path)
    separator = _detect_separator(file_path, encoding)
    rows_as_text: List[str] = []
    source_mapping = _resolve_source_mapping(file_path)
    priority_cols = source_mapping.get("priority_columns", {})
    focus_columns = source_mapping.get("focus_columns", [])
    include_other_columns = bool(source_mapping.get("include_other_columns", True))

    with file_path.open("r", encoding=encoding, errors="replace", newline="") as file:
        reader = csv.DictReader(file, delimiter=separator)
        if reader.fieldnames:
            medical_cols = _detect_medical_columns(reader.fieldnames)

            for row in reader:
                normalized_row = {
                    _normalize_colname(str(key)): value
                    for key, value in row.items()
                    if key is not None
                }

                parts: List[str] = []
                used_keys = set()

                if isinstance(focus_columns, list) and focus_columns:
                    for col in focus_columns:
                        if col in normalized_row and _is_valid_cell(normalized_row[col]):
                            label = str(priority_cols.get(col, col.upper()))
                            parts.append(f"[{label}] {str(normalized_row[col]).strip()}")
                            used_keys.add(col)

                    if parts and not include_other_columns:
                        rows_as_text.append(" | ".join(parts))
                        continue

                for col, label in priority_cols.items():
                    if col in normalized_row and _is_valid_cell(normalized_row[col]):
                        parts.append(f"[{label}] {str(normalized_row[col]).strip()}")
                        used_keys.add(col)

                if not parts:
                    has_medical = any(medical_cols[cat] for cat in ["indication", "posology", "contraindication"])
                    if has_medical:
                        for category in ["product", "indication", "posology", "contraindication", "side_effect", "composition"]:
                            for field in medical_cols.get(category, []):
                                value = row.get(field, "")
                                if _is_valid_cell(value):
                                    label = category.upper().replace("_", " ")
                                    parts.append(f"[{label}] {str(value).strip()}")
                                    used_keys.add(field)

                for key, value in row.items():
                    key_norm = _normalize_colname(str(key)) if key is not None else ""
                    if key_norm in used_keys:
                        continue
                    if not include_other_columns:
                        continue
                    if _is_valid_cell(value):
                        parts.append(f"{key}: {str(value).strip()}")

                if parts:
                    rows_as_text.append(" | ".join(parts))

            return rows_as_text

    with file_path.open("r", encoding=encoding, errors="replace", newline="") as file:
        reader = csv.reader(file, delimiter=separator)
        headers = next(reader, [])
        for row in reader:
            parts = []
            for index, value in enumerate(row):
                if not _is_valid_cell(value):
                    continue
                clean_value = str(value).strip()
                if index < len(headers) and str(headers[index]).strip():
                    parts.append(f"{headers[index]}: {clean_value}")
                else:
                    parts.append(clean_value)
            if parts:
                rows_as_text.append(" | ".join(parts))
    return rows_as_text


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    chunks: List[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _collect_docs(docs_dir: Path) -> List[Dict[str, str]]:
    if not docs_dir.exists():
        raise FileNotFoundError(f"Dossier de documents introuvable: {docs_dir}")

    records: List[Dict[str, str]] = []
    for file_path in docs_dir.rglob("*"):
        if not file_path.is_file():
            continue
        ext = file_path.suffix.lower()
        if ext not in {".pdf", ".txt", ".csv"}:
            continue

        if ext == ".csv":
            rows = _read_csv_rows(file_path)
            for row_idx, row_text in enumerate(rows):
                for chunk_idx, chunk in enumerate(_chunk_text(row_text, chunk_size=700, overlap=120)):
                    records.append(
                        {
                            "id": f"{file_path.name}::row_{row_idx}::chunk_{chunk_idx}",
                            "source": str(file_path),
                            "text": chunk,
                        }
                    )
            continue

        text = _read_pdf(file_path) if ext == ".pdf" else _read_txt(file_path)
        for idx, chunk in enumerate(_chunk_text(text)):
            records.append(
                {
                    "id": f"{file_path.name}::chunk_{idx}",
                    "source": str(file_path),
                    "text": chunk,
                }
            )
    if not records:
        raise ValueError("Aucun contenu PDF/TXT/CSV exploitable trouvé.")
    return records


def build_index(
    docs_dir: Path,
    index_dir: Path,
    collection_name: str = "medical_docs",
    embedding_model: str = "default",
) -> None:
    records = _collect_docs(docs_dir)

    index_dir.mkdir(parents=True, exist_ok=True)
    with (index_dir / "chunks.json").open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    if embedding_model.strip().lower() == "default":
        embedding_function = embedding_functions.ONNXMiniLM_L6_V2()
    else:
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
        )

    os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")

    def _new_client() -> chromadb.PersistentClient:
        return chromadb.PersistentClient(
            path=str(index_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _cleanup_chroma_storage() -> None:
        for item in index_dir.iterdir():
            if item.name == "chunks.json":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink()
                except FileNotFoundError:
                    pass

    client = _new_client()
    try:
        client.delete_collection(name=collection_name)
    except Exception as exc:
        message = str(exc).lower()
        collection_missing = (
            "not found" in message
            or "does not exist" in message
            or "invalidcollectionexception" in message
        )
        if not collection_missing:
            _cleanup_chroma_storage()
            client = _new_client()

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [record["id"] for record in records]
    documents = [record["text"] for record in records]
    metadatas = [
        {
            "id": record["id"],
            "source": record["source"],
        }
        for record in records
    ]

    batch_size = 128
    for start in range(0, len(records), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )