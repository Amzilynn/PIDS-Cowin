"""
Script de nettoyage de la table delegates apres la migration vers users.
- Supprime last_login et created_at de delegates (maintenant dans users)
- Ajoute la contrainte FK delegates.id -> users.id
- Retire AUTO_INCREMENT de delegates.id

Usage : python fix_delegates_table.py
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from shared.database import engine


def fix_delegates():
    print("=" * 60)
    print("[START] Nettoyage de la table delegates...")
    print("=" * 60)

    with engine.connect() as conn:

        # ------------------------------------------------------------------
        # 1. Verifier si last_login existe encore dans delegates
        # ------------------------------------------------------------------
        has_last_login = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'delegates'
              AND COLUMN_NAME  = 'last_login'
        """)).scalar()

        if has_last_login:
            conn.execute(text("ALTER TABLE delegates DROP COLUMN last_login"))
            conn.commit()
            print("[OK] Colonne last_login supprimee de delegates")
        else:
            print("[INFO] last_login deja absent de delegates")

        # ------------------------------------------------------------------
        # 2. Verifier si created_at existe encore dans delegates
        # ------------------------------------------------------------------
        has_created_at = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'delegates'
              AND COLUMN_NAME  = 'created_at'
        """)).scalar()

        if has_created_at:
            conn.execute(text("ALTER TABLE delegates DROP COLUMN created_at"))
            conn.commit()
            print("[OK] Colonne created_at supprimee de delegates")
        else:
            print("[INFO] created_at deja absent de delegates")

        # ------------------------------------------------------------------
        # 3. Verifier si la FK existe deja
        # ------------------------------------------------------------------
        has_fk = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA        = DATABASE()
              AND TABLE_NAME          = 'delegates'
              AND COLUMN_NAME         = 'id'
              AND REFERENCED_TABLE_NAME = 'users'
        """)).scalar()

        if not has_fk:
            try:
                # Retirer AUTO_INCREMENT d'abord
                conn.execute(text("""
                    ALTER TABLE delegates
                    MODIFY COLUMN id INT NOT NULL
                """))
                conn.commit()
                print("[OK] AUTO_INCREMENT retire de delegates.id")

                # Ajouter la FK
                conn.execute(text("""
                    ALTER TABLE delegates
                    ADD CONSTRAINT fk_delegates_users
                    FOREIGN KEY (id) REFERENCES users(id)
                    ON DELETE CASCADE
                """))
                conn.commit()
                print("[OK] Contrainte FK delegates.id -> users.id ajoutee")
            except Exception as e:
                print(f"[WARN] FK non ajoutee (peut-etre deja presente) : {e}")
        else:
            print("[INFO] FK delegates.id -> users.id deja presente")

        # ------------------------------------------------------------------
        # 4. Verifier la structure finale de delegates
        # ------------------------------------------------------------------
        cols = conn.execute(text("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'delegates'
            ORDER BY ORDINAL_POSITION
        """)).fetchall()

        print("\n[INFO] Structure finale de la table delegates :")
        print(f"  {'Colonne':<30} {'Type':<20} {'Nullable':<10} {'Key'}")
        print("  " + "-" * 65)
        for col in cols:
            print(f"  {col[0]:<30} {col[1]:<20} {col[2]:<10} {col[3]}")

    print("\n" + "=" * 60)
    print("[DONE] Nettoyage termine !")
    print("=" * 60)


if __name__ == "__main__":
    fix_delegates()
