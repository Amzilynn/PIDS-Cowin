from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import json
import re
import pickle
import csv

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer


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
        field_lower = field.lower().strip()
        for category, keywords in medical_keywords.items():
            if any(keyword in field_lower for keyword in keywords):
                detected[category].append(field)
                break
    return detected


def _read_csv_rows(file_path: Path) -> List[str]:
    rows_as_text: List[str] = []
    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames:
            medical_cols = _detect_medical_columns(reader.fieldnames)
            has_medical = any(medical_cols[cat] for cat in ["indication", "posology"])
            
            for row in reader:
                if has_medical:
                    product_name = ""
                    for field in medical_cols.get("product", []):
                        if field in row and row[field]:
                            product_name = str(row[field]).strip()
                            break
                    
                    parts = []
                    if product_name:
                        parts.append(f"PRODUIT: {product_name}")
                    
                    for category in ["indication", "posology", "contraindication", "side_effect", "composition"]:
                        for field in medical_cols.get(category, []):
                            value = row.get(field, "")
                            if value and str(value).strip():
                                label = category.upper().replace("_", " ")
                                parts.append(f"[{label}] {str(value).strip()}")
                    
                    for key, value in row.items():
                        if key and value and str(value).strip():
                            if key not in sum(medical_cols.values(), []):
                                parts.append(f"{key}: {str(value).strip()}")
                    
                    if parts:
                        rows_as_text.append(" | ".join(parts))
                else:
                    parts = [
                        f"{key}: {str(value).strip()}"
                        for key, value in row.items()
                        if key and value and str(value).strip()
                    ]
                    if parts:
                        rows_as_text.append(" | ".join(parts))
            return rows_as_text

    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        reader = csv.reader(file)
        headers = next(reader, [])
        for row in reader:
            parts = []
            for index, value in enumerate(row):
                clean_value = str(value).strip()
                if not clean_value:
                    continue
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


def build_index(docs_dir: Path, index_dir: Path) -> None:
    records = _collect_docs(docs_dir)
    corpus = [record["text"] for record in records]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=60000)
    matrix = vectorizer.fit_transform(corpus)

    index_dir.mkdir(parents=True, exist_ok=True)
    with (index_dir / "chunks.json").open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    with (index_dir / "vectorizer.pkl").open("wb") as file:
        pickle.dump(vectorizer, file)

    with (index_dir / "tfidf.pkl").open("wb") as file:
        pickle.dump(matrix, file)