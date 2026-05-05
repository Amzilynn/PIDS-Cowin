import sys
import os

# Ajout du chemin pour trouver le dossier shared
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.database import SessionLocal
from shared.models import Gamme

def create_gammes(names_list):
    db = SessionLocal()
    print("🚀 Création des gammes dans la base de données...")
    
    for name in names_list:
        name = name.strip()
        # On vérifie si elle existe déjà
        exists = db.query(Gamme).filter(Gamme.name == name).first()
        if not exists:
            new_gamme = Gamme(name=name)
            db.add(new_gamme)
            print(f"✅ Gamme créée : {name}")
        else:
            print(f"⏩ Gamme déjà existante : {name}")
            
    db.commit()
    db.close()
    print("✨ Opération terminée.")

if __name__ == "__main__":
    # METTEZ VOS NOMS DE GAMMES (PowerPoints) ICI
    mes_gammes = [
        "Bactol",
        "Calmoss",
        "Cosmopharma",
        "Ferbiotic",
        "Healthcare",
        "Hydra",
        "Minciligne",
        "Mincivit",
        "Oligovit",
        "Omevie",
        "Pediakids",
        "Phytol",
        "Phytophane",
        "Phytothera",
        "Plantherapie",
        "TC2000 & SPS",
        "Tidol",
        "Uniderm",
        "Vitonic",
        "Vitosine",
        "Vital"

    ]
    
    create_gammes(mes_gammes)
