from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from dso3.database import SessionLocal
from dso3.models.delegate import Delegate
from dso3.models.product import Product
from dso3.services.embedding import cosine, get_embedding


@dataclass
class EvalRow:
    product_id: int
    true_delegate_ids: set[int]


def _parse_delegate_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    normalized = raw.replace("|", ",").replace(";", ",")
    values: set[int] = set()
    for item in normalized.split(","):
        item = item.strip()
        if not item:
            continue
        values.add(int(item))
    return values


def load_manifest(csv_path: Path) -> list[EvalRow]:
    rows: list[EvalRow] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_raw = row.get("product_id", "").strip()
            true_one = row.get("true_delegate_id", "").strip()
            true_many = row.get("true_delegate_ids", "").strip()

            if not product_raw:
                continue

            product_id = int(product_raw)
            true_ids = _parse_delegate_ids(true_many)
            if true_one:
                true_ids.add(int(true_one))

            if not true_ids:
                continue

            rows.append(EvalRow(product_id=product_id, true_delegate_ids=true_ids))
    return rows


def _rank_delegates_for_product(product: Product, delegates: list[Delegate]) -> list[int]:
    product_text = f"{product.category} {product.description}".strip()
    product_vec = get_embedding(product_text)

    scored: list[tuple[int, float]] = []
    for delegate in delegates:
        delegate_text = f"{delegate.expertise} {delegate.interests} {delegate.specification or ''}".strip()
        delegate_vec = get_embedding(delegate_text)
        score = float(cosine(product_vec, delegate_vec))
        scored.append((delegate.id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [delegate_id for delegate_id, _score in scored]


def evaluate(manifest_path: Path, k: int = 1) -> dict:
    if k < 1:
        raise ValueError("k must be >= 1")

    samples = load_manifest(manifest_path)
    if not samples:
        raise ValueError("No valid rows found in manifest")

    db = SessionLocal()
    try:
        delegates = db.query(Delegate).all()
        if not delegates:
            raise ValueError("No delegates found in database")

        top1_hits = 0
        precision_sum = 0.0
        recall_sum = 0.0
        evaluated = 0
        skipped = 0

        for sample in samples:
            product = db.query(Product).filter(Product.id == sample.product_id).first()
            if product is None:
                skipped += 1
                continue

            ranked_delegate_ids = _rank_delegates_for_product(product, delegates)
            pred_topk = ranked_delegate_ids[:k]
            if not pred_topk:
                skipped += 1
                continue

            evaluated += 1
            if pred_topk[0] in sample.true_delegate_ids:
                top1_hits += 1

            overlap = len(set(pred_topk).intersection(sample.true_delegate_ids))
            precision_sum += overlap / float(k)
            recall_sum += overlap / float(len(sample.true_delegate_ids))

        if evaluated == 0:
            raise ValueError("No rows could be evaluated (check product_ids in CSV)")

        return {
            "manifest": str(manifest_path),
            "k": k,
            "samples_total": len(samples),
            "samples_evaluated": evaluated,
            "samples_skipped": skipped,
            "accuracy_top1": round(top1_hits / evaluated, 4),
            "precision_at_k": round(precision_sum / evaluated, 4),
            "recall_at_k": round(recall_sum / evaluated, 4),
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate DSO3 recommendation metrics")
    parser.add_argument("--csv", required=True, type=str, help="Path to ground-truth CSV")
    parser.add_argument("--k", default=1, type=int, help="Top-k for precision/recall")
    parser.add_argument("--output", type=str, help="Optional output JSON path")
    args = parser.parse_args()

    report = evaluate(Path(args.csv), k=args.k)

    print("\n=== DSO3 Recommendation Metrics ===")
    print(f"CSV               : {report['manifest']}")
    print(f"k                 : {report['k']}")
    print(f"Samples (total)   : {report['samples_total']}")
    print(f"Samples (eval)    : {report['samples_evaluated']}")
    print(f"Samples (skipped) : {report['samples_skipped']}")
    print(f"Top-1 Accuracy    : {report['accuracy_top1']:.4f}")
    print(f"Precision@k       : {report['precision_at_k']:.4f}")
    print(f"Recall@k          : {report['recall_at_k']:.4f}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to {output_path}")


if __name__ == "__main__":
    main()