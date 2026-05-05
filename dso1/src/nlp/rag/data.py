# rag/data.py
import csv
import json
import os
from pathlib import Path

# __file__ is dso1/src/nlp/rag/data.py
DSO1_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = DSO1_ROOT / "Data"

csv_path = DATA_DIR / "vital_products.csv"
json_path = DATA_DIR / "vital_products.json"

def csv_to_json():
    products = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                "url": row.get("url", ""),
                "name": row.get("name", ""),
                "categories": row.get("categories", ""),
                "image": row.get("image", ""),
                "indications": row.get("indications", ""),
                "forme": row.get("forme", ""),
                "infos_sur_le_produit": row.get("infos_sur_le_produit", ""),
                "classe": row.get("classe", ""),
                "compositions": row.get("compositions", ""),
                "conseils": row.get("conseils_d'utilisation", ""),
                "contre_indications": row.get("contre-indications", "")
            })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print("JSON créé :", json_path)