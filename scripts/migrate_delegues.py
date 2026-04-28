import csv
import sys
import os

# Ajout du chemin pour trouver le dossier shared
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.database import SessionLocal
from shared.models import Delegate

def migrate():
    db = SessionLocal()
    csv_path = "dso1/Data/delegues.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Fichier {csv_path} introuvable.")
        return

    print("Migration des delegues vers la base de donnees...")
    
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nom = row['Nom']
            # On vérifie si le délégué existe déjà pour éviter les doublons
            exists = db.query(Delegate).filter(Delegate.first_name == nom).first()
            
            if not exists:
                # Logique de rôle par défaut pour votre test
                role = "Commercial" if nom == "Samar" else "Medical"
                
                # Mapping des niveaux (CSV -> SQL)
                level_map = {
                    "Beginner": "Débutant",
                    "Intermediate": "Junior",
                    "Expert": "Expert"
                }
                level = level_map.get(row['Level'], "Débutant")

                new_delegate = Delegate(
                    first_name=nom,
                    last_name="Test",
                    email=f"{nom.lower()}@avalive.fr",
                    password_hash="pbkdf2:sha256:...", # Mot de passe par défaut
                    role=role,
                    current_level=level,
                    global_score=float(row['Score'])
                )
                db.add(new_delegate)
                print(f"Ajoute : {nom} ({role}, {level})")
            else:
                print(f"Deja present : {nom}")

    db.commit()
    db.close()
    print("Migration terminee !")

if __name__ == "__main__":
    migrate()
