"""
Seed script — Loads existing CSV data into the DSO4 MySQL tables.

Usage:
    python scripts/seed_dso4.py

Prerequisites:
    1. Run  python scripts/migrate_dso4.py  first to create the tables.
    2. CSV files must exist at their expected locations:
       - dso4/data/delegues.csv
       - dso4/data/visites.csv
       - dso2/data/raw/medecins.csv
       - dso2/data/raw/pharmacies.csv
"""

import sys
import os
import csv
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import SessionLocal
from shared.modelsDSO4 import (
    DelegueDSO4,
    MedecinDSO4,
    PharmacienDSO4,
    VisiteDSO4,
)

# ─── CSV Paths ───────────────────────────────────────────────────
DSO4_DATA = os.path.join(PROJECT_ROOT, "dso4", "data")
DSO2_DATA = os.path.join(PROJECT_ROOT, "dso2", "data", "raw")

DELEGUES_CSV = os.path.join(DSO4_DATA, "delegues.csv")
VISITES_CSV = os.path.join(DSO4_DATA, "visites.csv")
MEDECINS_CSV = os.path.join(DSO2_DATA, "medecins.csv")
PHARMACIES_CSV = os.path.join(DSO2_DATA, "pharmacies.csv")


# ─── CSV Reader Helper ───────────────────────────────────────────
def read_csv(path: str) -> list[dict]:
    """Read a CSV file with BOM handling, return list of dicts."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return list(csv.DictReader(f))


def safe_float(val, default=None):
    """Convert to float safely, return default on failure."""
    try:
        return float(val) if val and str(val).strip() else default
    except (ValueError, TypeError):
        return default


def safe_int(val, default=None):
    """Convert to int safely, return default on failure."""
    try:
        return int(val) if val and str(val).strip() else default
    except (ValueError, TypeError):
        return default


# ─── Seed Functions ──────────────────────────────────────────────

def seed_delegues(db):
    """Load dso4/data/delegues.csv → delegues_dso4 table."""
    if not os.path.exists(DELEGUES_CSV):
        print(f"  ⚠️  File not found: {DELEGUES_CSV}")
        return 0

    rows = read_csv(DELEGUES_CSV)
    count = 0
    for r in rows:
        obj = DelegueDSO4(
            id=int(r["id"]),
            nom=r.get("nom", ""),
            prenom=r.get("prenom", ""),
            email=r.get("email", ""),
            zone=r.get("zone"),
            ville=r.get("ville"),
            latitude=safe_float(r.get("latitude")),
            longitude=safe_float(r.get("longitude")),
            disponibilite=r.get("disponibilite"),
        )
        db.merge(obj)  # merge = insert or update if exists
        count += 1

    db.commit()
    return count


def seed_medecins(db):
    """Load dso2/data/raw/medecins.csv → medecins_dso4 table."""
    if not os.path.exists(MEDECINS_CSV):
        print(f"  ⚠️  File not found: {MEDECINS_CSV}")
        return 0

    rows = read_csv(MEDECINS_CSV)
    count = 0
    for r in rows:
        obj = MedecinDSO4(
            id=int(r["id"]),
            nom=r.get("nom", ""),
            prenom=r.get("prenom", ""),
            specialite=r.get("specialite", ""),
            telephone=r.get("telephone", ""),
            email=r.get("email", ""),
            adresse=r.get("adresse", ""),
            latitude=safe_float(r.get("latitude")),
            longitude=safe_float(r.get("longitude")),
        )
        db.merge(obj)
        count += 1

    db.commit()
    return count


def seed_pharmaciens(db):
    """Load dso2/data/raw/pharmacies.csv → pharmaciens_dso4 table."""
    if not os.path.exists(PHARMACIES_CSV):
        print(f"  ⚠️  File not found: {PHARMACIES_CSV}")
        return 0

    rows = read_csv(PHARMACIES_CSV)
    count = 0
    for r in rows:
        # Map CSV column "type" → type_pharmacie
        ptype = r.get("type", "jour").strip().lower()
        if ptype not in ("jour", "nuit"):
            ptype = "jour"

        obj = PharmacienDSO4(
            id=int(r["id"]),
            nom=r.get("nom", ""),
            type_pharmacie=ptype,
            telephone=r.get("telephone", ""),
            adresse=r.get("adresse", ""),
            gouvernorat=r.get("gouvernorat", ""),
            url=r.get("url", ""),
            latitude=safe_float(r.get("latitude")),    # ← ADD THIS
            longitude=safe_float(r.get("longitude")),  # ← ADD THIS
        )
        db.merge(obj)
        count += 1

    db.commit()
    return count


def seed_visites(db):
    """Load dso4/data/visites.csv → visites_dso4 table."""
    if not os.path.exists(VISITES_CSV):
        print(f"  ⚠️  File not found: {VISITES_CSV}")
        return 0

    rows = read_csv(VISITES_CSV)
    count = 0
    skipped = 0

    for r in rows:
        try:
            # Parse date
            date_str = r.get("date", "").strip()
            visit_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Normalize statut
            statut = r.get("statut", "planifiee").strip().lower()
            statut_map = {
                "effectuee": "effectuée",
                "effectuée": "effectuée",
                "annulee": "annulée",
                "annulée": "annulée",
                "reportee": "reportée",
                "reportée": "reportée",
                "planifiee": "planifiee",
                "planifiée": "planifiee",
            }
            statut = statut_map.get(statut, "planifiee")

            # Normalize type_visite
            type_v = r.get("type_visite", "physique").strip().lower()
            if type_v not in ("physique", "en_ligne"):
                type_v = "physique"

            obj = VisiteDSO4(
                id=int(r["id"]),
                delegue_id=int(r["delegue_id"]),
                medecin_id=int(r["medecin_id"]),
                date=visit_date,
                heure=r.get("heure", ""),
                duree_min=safe_int(r.get("duree_min")),
                statut=statut,
                type_visite=type_v,
                score_visite=safe_float(r.get("score_visite")),
                distance_km=safe_float(r.get("distance_km")),
                specialite_medecin=r.get("specialite_medecin", ""),
            )
            db.merge(obj)
            count += 1
        except Exception as e:
            skipped += 1
            continue

    db.commit()
    if skipped:
        print(f"  ⚠️  Skipped {skipped} rows with errors")
    return count


# ─── Main ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  DSO4 — Seed Database from CSV Files")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        # Seed in order (respecting foreign key dependencies)
        n = seed_delegues(db)
        print(f"  ✅ delegues_dso4       → {n} rows inserted")

        n = seed_medecins(db)
        print(f"  ✅ medecins_dso4       → {n} rows inserted")

        n = seed_pharmaciens(db)
        print(f"  ✅ pharmaciens_dso4    → {n} rows inserted")

        n = seed_visites(db)
        print(f"  ✅ visites_dso4        → {n} rows inserted")

        print()
        print("  🎉 All data seeded successfully!")
        print("  Open phpMyAdmin to verify the records.")

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error: {e}")
        print()
        print("  Did you run  python scripts/migrate_dso4.py  first?")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
