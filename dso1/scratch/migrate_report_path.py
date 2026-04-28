import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Vérifier si la colonne existe déjà
            conn.execute(text("ALTER TABLE simulations ADD COLUMN report_path VARCHAR(512)"))
            conn.commit()
            print("SUCCESS: Colonne 'report_path' ajoutee.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("INFO: La colonne 'report_path' existe deja.")
            else:
                print(f"ERROR migration : {e}")

if __name__ == "__main__":
    migrate()
