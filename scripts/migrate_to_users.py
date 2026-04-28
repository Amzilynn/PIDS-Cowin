"""
Script de migration : cree la table `users` et migre les delegues existants.
Cree aussi les tables enfants (medecins, pharmaciens, admins) vides.

Usage : python migrate_to_users.py
"""

import sys
import os
import io
from passlib.context import CryptContext

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.database import engine, Base, SessionLocal
from shared import models  # importe tous les modèles pour que Base les connaisse

# Contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def migrate():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("[START] Migration : creation des nouvelles tables...")
        print("=" * 60)

        # ---------------------------------------------------------------
        # 1. Cree toutes les nouvelles tables (users, medecins, pharmaciens,
        #    admins) si elles n'existent pas encore.
        #    Les tables existantes (delegates, products, simulations...) ne
        #    sont PAS touchees grace a checkfirst=True implicite.
        # ---------------------------------------------------------------
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées (ou déjà existantes)")

        # ---------------------------------------------------------------
        # 2. Créer un compte Admin par défaut s'il n'existe pas déjà
        # ---------------------------------------------------------------
        existing_admin = db.query(models.User).filter(
            models.User.email == "admin@avalive.tn"
        ).first()

        if not existing_admin:
            admin = models.Admin(
                email="admin@avalive.tn",
                password_hash=pwd_context.hash("Admin@2025"),
                type="admin",
                display_name="Super Administrateur",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"✅ Admin créé  → email: admin@avalive.tn  | pass: Admin@2025")
        else:
            print(f"ℹ️  Admin déjà présent (id={existing_admin.id})")

        # ---------------------------------------------------------------
        # 3. Migrer les délégués existants qui n'ont pas encore de User
        #    (on lit email + password_hash directement depuis la vieille
        #     colonne de la table delegates via SQL brut, avant la suppression)
        # ---------------------------------------------------------------
        print("\n📦 Migration des délégués existants...")

        # Lecture SQL brut pour récupérer les anciennes colonnes
        from sqlalchemy import text
        try:
            old_delegates = engine.execute(
                text("SELECT id, email, password_hash FROM delegates WHERE email IS NOT NULL")
            ).fetchall()
        except Exception:
            # Si les colonnes email/password_hash ont déjà été supprimées
            # ou si la commande échoue (SQLAlchemy 2.x)
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id, email, password_hash FROM delegates WHERE email IS NOT NULL")
                )
                old_delegates = result.fetchall()

        migrated = 0
        for row in old_delegates:
            delegate_id, email, password_hash = row[0], row[1], row[2]

            # Vérifie si un User existe déjà pour cet email
            existing = db.query(models.User).filter(
                models.User.email == email
            ).first()
            if existing:
                print(f"  ⏭️  {email} → déjà migré")
                continue

            # Crée l'entrée dans users en réutilisant le même id
            # Note : on insère en SQL brut pour forcer l'id correspondant
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO users (id, email, password_hash, type, is_active)
                        VALUES (:id, :email, :pass, 'delegue', 1)
                        ON DUPLICATE KEY UPDATE email=email
                    """),
                    {"id": delegate_id, "email": email, "pass": password_hash}
                )
                conn.commit()

            migrated += 1
            print(f"  ✅ {email} → migré vers users (id={delegate_id})")

        print(f"\n✅ {migrated} délégué(s) migré(s) vers la table users")

        # ---------------------------------------------------------------
        # 4. Supprimer les colonnes email et password_hash de delegates
        #    (seulement si la migration des données est terminée)
        # ---------------------------------------------------------------
        if migrated > 0 or len(old_delegates) > 0:
            print("\n🔧 Suppression des colonnes email/password_hash de delegates...")
            try:
                with engine.connect() as conn:
                    # Vérifie si la colonne email existe encore
                    col_check = conn.execute(
                        text("""
                            SELECT COUNT(*) FROM information_schema.COLUMNS
                            WHERE TABLE_SCHEMA = DATABASE()
                            AND TABLE_NAME = 'delegates'
                            AND COLUMN_NAME = 'email'
                        """)
                    ).scalar()

                    if col_check > 0:
                        conn.execute(text("ALTER TABLE delegates DROP COLUMN email"))
                        conn.execute(text("ALTER TABLE delegates DROP COLUMN password_hash"))
                        conn.commit()
                        print("  ✅ Colonnes email + password_hash supprimées de delegates")
                    else:
                        print("  ℹ️  Colonnes déjà supprimées.")
            except Exception as e:
                print(f"  ⚠️  Impossible de supprimer les colonnes : {e}")
                print("       Fais-le manuellement dans phpMyAdmin si nécessaire.")

        print("\n" + "=" * 60)
        print("🎉 Migration terminée avec succès !")
        print("=" * 60)
        print("\nComptes disponibles pour les tests :")
        print("  Admin     → admin@avalive.tn        | Admin@2025")
        print("\nAjoute des médecins/pharmaciens manuellement dans phpMyAdmin")
        print("ou via le script create_test_users.py")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur lors de la migration : {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
