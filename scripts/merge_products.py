import csv
import sys
import os

# Ajout du chemin pour trouver le dossier shared
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.database import SessionLocal
from shared.models import Gamme, Product

def merge_csv_remaining():
    db = SessionLocal()
    csv_path = "dso1/Data/vital_products.csv"
    
    if not os.path.exists(csv_path):
        print(f"Erreur : {csv_path} introuvable.")
        return

    # 1. On récupère toutes les gammes pour faire le matching
    gammes = db.query(Gamme).all()
    gamme_map = {g.name.lower(): g.id for g in gammes}
    vital_id = gamme_map.get("vital") # Gamme par défaut

    print(f"Démarrage de l'import CSV (Matching sur {len(gamme_map)} gammes)...")

    count_added = 0
    count_skipped = 0

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_name = row['name'].strip()
            
            # 2. VÉRIFICATION : Si le produit existe déjà, on ne touche à rien
            exists = db.query(Product).filter(Product.name == full_name).first()
            if exists:
                count_skipped += 1
                continue

            # 3. DÉTERMINATION DE LA GAMME
            found_gamme_id = None
            # On cherche si un nom de gamme est présent dans le nom du produit
            for g_name, g_id in gamme_map.items():
                if g_name != "vital" and g_name in full_name.lower():
                    found_gamme_id = g_id
                    break
            
            # 4. REPLI : Si pas trouvé, on affecte à "Vital"
            if not found_gamme_id:
                found_gamme_id = vital_id

            # 5. DESCRIPTION
            # On stocke les infos utiles du CSV
            description = f"Indications: {row.get('indications', 'N/A')}\nForme: {row.get('forme', 'N/A')}\nCompositions: {row.get('compositions', 'N/A')}"

            new_product = Product(
                name=full_name,
                gamme_id=found_gamme_id,
                description=description
            )
            db.add(new_product)
            count_added += 1

    db.commit()
    db.close()
    print(f"\n✨ Import CSV terminé !")
    print(f"Nouveaux produits ajoutés : {count_added}")
    print(f"Produits déjà présents (ignorés) : {count_skipped}")

if __name__ == "__main__":
    merge_csv_remaining()
