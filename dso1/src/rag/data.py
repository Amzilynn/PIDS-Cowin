# rag/data.py
import csv
import json
import os

csv_path = "dso1/data/rag/vital_products.csv"
json_path = "dso1/data/rag/vital_products.json"

def csv_to_json():
    products = []

    for enc in ['utf-8', 'utf-16', 'latin-1']:
        try:
            with open(csv_path, encoding=enc) as f:
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
            break # Successfully read
        except UnicodeDecodeError:
            products = [] # Reset products if we need to retry with a new encoding
            continue

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print("JSON créé :", json_path)