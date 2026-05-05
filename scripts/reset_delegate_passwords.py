"""
Reinitialise les mots de passe des delegues existants avec un hash bcrypt valide.
A lancer APRES migrate_to_users.py

Les anciens hashes (pbkdf2:sha256:...) ne sont pas compatibles avec bcrypt/passlib.
Ce script leur assigne un nouveau mot de passe par defaut.

Usage : python reset_delegate_passwords.py
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from shared.database import SessionLocal
from shared import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mot de passe par defaut assigne aux anciens delegues
DEFAULT_PASSWORD = "Delegue@2025"


def reset_passwords():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("[START] Reinitialisation des mots de passe delegues...")
        print("=" * 60)

        # Recupere tous les users de type 'delegue'
        delegues = db.query(models.User).filter(
            models.User.type == "delegue"
        ).all()

        if not delegues:
            print("[INFO] Aucun delegue trouve dans la table users.")
            return

        updated = 0
        for user in delegues:
            # Verifier si le hash actuel est un hash bcrypt valide
            is_valid = False
            try:
                # Un hash bcrypt valide commence par $2b$ ou $2a$
                is_valid = user.password_hash.startswith(("$2b$", "$2a$"))
            except Exception:
                pass

            if is_valid:
                print(f"  [SKIP] {user.email} --> hash bcrypt valide, pas touche")
                continue

            # Remplacer par un hash bcrypt du mot de passe par defaut
            user.password_hash = pwd_context.hash(DEFAULT_PASSWORD)
            updated += 1
            print(f"  [OK] {user.email} --> mot de passe reinitialise")

        db.commit()

        print(f"\n[OK] {updated} delegue(s) mis a jour")
        print("\n" + "=" * 60)
        print("[DONE] Reinitialisation terminee !")
        print("=" * 60)

        if updated > 0:
            print(f"\nMot de passe par defaut : {DEFAULT_PASSWORD}")
            print("Dis a chaque delegue de le changer apres sa premiere connexion.")

        print("\n--- Comptes delegues disponibles ---")
        all_delegues = db.query(models.Delegate).all()
        for d in all_delegues:
            print(f"  {d.email:<35} | {d.first_name} {d.last_name} ({d.role})")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] : {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    reset_passwords()
