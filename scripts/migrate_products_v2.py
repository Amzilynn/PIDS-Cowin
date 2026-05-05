import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from shared.database import engine

def migrate():
    print("🚀 Début de la migration de la table 'products'...")
    
    with engine.connect() as conn:
        # Ajout des nouvelles colonnes si elles n'existent pas
        columns_to_add = [
            ("INDICATIONS", "TEXT"),
            ("COMPOSITION ", "TEXT"),
            ("CONSEILS D'UTILISATION", "TEXT")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                print(f"Adding column {col_name}...")
                conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"✅ Colonne {col_name} ajoutée.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"ℹ️ La colonne {col_name} existe déjà, on passe.")
                else:
                    print(f"❌ Erreur sur {col_name}: {e}")

    print("\n✨ Structure mise à jour avec succès !")

if __name__ == "__main__":
    migrate()
