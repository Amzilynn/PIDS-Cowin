from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Optional

from .models import ProductRecord


class ProductCatalog:
    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path
        self._products = self._load()

    @property
    def products(self) -> List[ProductRecord]:
        return self._products

    def search_by_name(self, query: str, limit: int = 20) -> List[ProductRecord]:
        query_norm = _normalize(query)
        if not query_norm:
            return self._products[:limit]

        matches: List[ProductRecord] = []
        for product in self._products:
            if query_norm in _normalize(product.name):
                matches.append(product)
                if len(matches) >= limit:
                    break
        return matches

    def get_by_exact_name(self, name: str) -> Optional[ProductRecord]:
        target = _normalize(name)
        for product in self._products:
            if _normalize(product.name) == target:
                return product
        return None

    def _load(self) -> List[ProductRecord]:
        if not self._csv_path.exists():
            raise FileNotFoundError(f"Catalog not found: {self._csv_path}")

        products: List[ProductRecord] = []
        seen = set()

        with self._csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("name") or "").strip()
                url = (row.get("url") or "").strip()
                if not name:
                    continue

                dedupe_key = (_normalize(name), url)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                products.append(
                    ProductRecord(
                        url=url,
                        name=name,
                        categories=_split_categories(row.get("categories") or ""),
                        image=(row.get("image") or "").strip(),
                        indications=(row.get("INDICATIONS") or "").strip(),
                        form=(row.get("FORME") or "").strip(),
                        product_info=(row.get("INFOS SUR LE PRODUIT") or "").strip(),
                        product_class=(row.get("CLASSE") or "").strip(),
                        composition=(row.get("COMPOSITIONS") or "").strip(),
                        usage_advice=(row.get("Conseils d'utilisation") or "").strip(),
                        contraindications=(row.get("CONTRE INDICATIONS") or "").strip(),
                    )
                )
        return products


def _split_categories(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())
