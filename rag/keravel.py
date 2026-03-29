import pandas as pd
import json

def csv_to_json(csv_path, json_path):
    df = pd.read_csv(csv_path)

    data = []

    for _, row in df.iterrows():
        item = {
            "product": row.get("Product", ""),
            "description": row.get("Description", ""),
            "ingredients": row.get("Ingredients", ""),
            "advice": row.get("Conseils", ""),
            "storage": row.get("Conservation", ""),
            "link": row.get("Link", "")
        }
        data.append(item)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("JSON created:", json_path)