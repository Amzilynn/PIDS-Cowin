import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.database import engine, Base
from shared.models import *

def init_db():
    print("🚀 Initialisation de la base de données partagée (Avalive)...")
    try:
        # Cette commande crée toutes les tables définies dans models.py
        # si elles n'existent pas déjà.
        Base.metadata.create_all(bind=engine)
        print("✅ Base de données initialisée avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")

if __name__ == "__main__":
    init_db()
