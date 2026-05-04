"""
Seed script — Loads existing CSV data into the MAIN MySQL tables (shared/models.py).
Generates access credentials (email and password) for all users.
"""

import sys
import os
import csv
from passlib.context import CryptContext

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import SessionLocal, engine, Base
from shared.models import User, Delegate, Medecin, Pharmacien

# ─── Configuration ──────────────────────────────────────────────────
DSO4_DATA = os.path.join(PROJECT_ROOT, "dso4", "data")
DSO2_DATA = os.path.join(PROJECT_ROOT, "dso2", "data", "raw")

DELEGUES_CSV = os.path.join(DSO4_DATA, "delegues.csv")
MEDECINS_CSV = os.path.join(DSO2_DATA, "medecins.csv")
PHARMACIES_CSV = os.path.join(DSO2_DATA, "pharmacies.csv")

DEFAULT_PASSWORD = "password123"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Helper Functions ───────────────────────────────────────────────
def read_csv(path: str) -> list[dict]:
    """Read a CSV file with BOM handling, return list of dicts."""
    if not os.path.exists(path):
        print(f"  [Warning] File not found: {path}")
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return list(csv.DictReader(f))

def safe_float(val, default=None):
    try:
        return float(val) if val and str(val).strip() else default
    except (ValueError, TypeError):
        return default

def generate_email(nom: str, prenom: str, index: int, domain="avalive.tn"):
    """Generates a clean email from nom and prenom."""
    n = str(nom).strip().lower().replace(" ", "")
    p = str(prenom).strip().lower().replace(" ", "")
    if p:
        base = f"{p}.{n}"
    else:
        base = f"{n}{index}"
    return f"{base}@{domain}"

# ─── Seed Logic ─────────────────────────────────────────────────────
def seed_delegates(db):
    rows = read_csv(DELEGUES_CSV)
    count = 0
    hashed_pwd = pwd_context.hash(DEFAULT_PASSWORD)
    inserted_emails = set()
    for r in rows:
        email = r.get("email", "").strip().lower()
        if not email:
            email = generate_email(r.get("nom", ""), r.get("prenom", ""), r.get("id"))
            
        if email in inserted_emails:
            continue
            
        # Check if exists in User table
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            obj = Delegate(
                email=email,
                password_hash=hashed_pwd,
                type="delegue",
                first_name=r.get("prenom", ""),
                last_name=r.get("nom", ""),
                address=r.get("ville", ""),
                latitude=safe_float(r.get("latitude")),
                longitude=safe_float(r.get("longitude"))
            )
            db.add(obj)
            inserted_emails.add(email)
            count += 1
    db.commit()
    return count

def seed_medecins(db):
    rows = read_csv(MEDECINS_CSV)
    count = 0
    hashed_pwd = pwd_context.hash(DEFAULT_PASSWORD)
    inserted_emails = set()
    for r in rows:
        email = r.get("email", "").strip().lower()
        if not email:
            email = generate_email(r.get("nom", ""), r.get("prenom", ""), r.get("id"))
            
        if email in inserted_emails:
            continue
            
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            obj = Medecin(
                email=email,
                password_hash=hashed_pwd,
                type="medecin",
                nom=r.get("nom", ""),
                prenom=r.get("prenom", ""),
                specialite=r.get("specialite", ""),
                telephone=r.get("telephone", ""),
                adresse=r.get("adresse", ""),
                latitude=safe_float(r.get("latitude")),
                longitude=safe_float(r.get("longitude"))
            )
            db.add(obj)
            inserted_emails.add(email)
            count += 1
    db.commit()
    return count

def seed_pharmaciens(db):
    rows = read_csv(PHARMACIES_CSV)
    count = 0
    hashed_pwd = pwd_context.hash(DEFAULT_PASSWORD)
    inserted_emails = set()
    for r in rows:
        email = generate_email(r.get("nom", ""), "pharmacie", r.get("id"))
            
        if email in inserted_emails:
            continue
            
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            ptype = r.get("type", "jour").strip().lower()
            if ptype not in ("jour", "nuit"):
                ptype = "jour"

            obj = Pharmacien(
                email=email,
                password_hash=hashed_pwd,
                type="pharmacien",
                nom=r.get("nom", ""),
                type_pharmacie=ptype,
                telephone=r.get("telephone", ""),
                adresse=r.get("adresse", ""),
                gouvernorat=r.get("gouvernorat", ""),
                url=r.get("url", ""),
                latitude=safe_float(r.get("latitude")),
                longitude=safe_float(r.get("longitude"))
            )
            db.add(obj)
            inserted_emails.add(email)
            count += 1
    db.commit()
    return count

# ─── Main ───────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Seeding MAIN Database with CSV Data")
    print("=" * 60)

    # Make sure all tables are created in the main schema
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        n = seed_delegates(db)
        print(f"  [OK] Delegates inserted: {n}")

        n = seed_medecins(db)
        print(f"  [OK] Medecins inserted: {n}")

        n = seed_pharmaciens(db)
        print(f"  [OK] Pharmaciens inserted: {n}")
        
        print("\n  [Success] All data seeded successfully into the main schema!")
        print(f"  Default password for new users: {DEFAULT_PASSWORD}")

    except Exception as e:
        db.rollback()
        print(f"  [Error] {repr(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
