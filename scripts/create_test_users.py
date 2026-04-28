"""
Script pour creer des utilisateurs de test (medecins, pharmaciens, delegues, admin).
A lancer APRES migrate_to_users.py

Usage : python create_test_users.py
"""

import sys
import os
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from shared.database import SessionLocal
from shared import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_test_users():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("[START] Creation des utilisateurs de test...")
        print("=" * 60)

        test_users = []

        # ------------------------------------------------------------------
        # Medecins de test (colonnes: nom, prenom, specialite, tel, adresse, lat, lng)
        # ------------------------------------------------------------------
        medecins_data = [
            {
                "email": "ghassenbf@yahoo.fr",
                "password": "Medecin@123",
                "nom": "BEN FRAJ",
                "prenom": "Ghassen",
                "specialite": "Ophtalmologie",
                "telephone": "20338549",
                "adresse": "Immeuble Ildo 02, Tunis",
                "latitude": 37.2705248,
                "longitude": 9.8698072,
            },
            {
                "email": "leila.boukadida@avalive.tn",
                "password": "Medecin@123",
                "nom": "BOUKADIDA BEN NACEUR",
                "prenom": "Leila",
                "specialite": "Psychiatrie",
                "telephone": "",
                "adresse": "Avenue Habib Bourguiba, Ariana",
                "latitude": 35.8312263,
                "longitude": 10.6403415,
            },
        ]

        # ------------------------------------------------------------------
        # Pharmaciens de test
        # Note: email genere automatiquement car absent du CSV
        # ------------------------------------------------------------------
        pharmaciens_data = [
            {
                "email": "farah.zgolli@avalive.tn",
                "password": "Pharma@123",
                "nom": "FARAH ZGOLLI",
                "type_pharmacie": "jour",
                "telephone": "+216 71 223 674",
                "adresse": "PLACE DE L'INDEPENDANCE, Ariana",
                "gouvernorat": "Ariana",
                "url": "https://www.med.tn/pharmacies/farah-zgolli",
            },
            {
                "email": "hela.benayed@avalive.tn",
                "password": "Pharma@123",
                "nom": "Hela Ben Ayed",
                "type_pharmacie": "jour",
                "telephone": "+216 71 856 356",
                "adresse": "555, Route de Raoued, Ariana",
                "gouvernorat": "Ariana",
                "url": "https://www.med.tn/pharmacies/hela-ben-ayed",
            },
        ]

        # ------------------------------------------------------------------
        # Creation des medecins
        # ------------------------------------------------------------------
        print("\n[Medecins]")
        for data in medecins_data:
            existing = db.query(models.User).filter(models.User.email == data["email"]).first()
            if existing:
                print(f"  [SKIP] {data['email']} --> deja existant")
                continue

            medecin = models.Medecin(
                email=data["email"],
                password_hash=pwd_context.hash(data["password"]),
                type="medecin",
                nom=data["nom"],
                prenom=data["prenom"],
                specialite=data["specialite"],
                telephone=data["telephone"],
                adresse=data["adresse"],
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
            )
            db.add(medecin)
            test_users.append({"role": "Medecin", "email": data["email"], "password": data["password"]})
            print(f"  [OK] Dr. {data['prenom']} {data['nom']} --> {data['email']}")

        # ------------------------------------------------------------------
        # Creation des pharmaciens
        # ------------------------------------------------------------------
        print("\n[Pharmaciens]")
        for data in pharmaciens_data:
            existing = db.query(models.User).filter(models.User.email == data["email"]).first()
            if existing:
                print(f"  [SKIP] {data['email']} --> deja existant")
                continue

            pharmacien = models.Pharmacien(
                email=data["email"],
                password_hash=pwd_context.hash(data["password"]),
                type="pharmacien",
                nom=data["nom"],
                type_pharmacie=data["type_pharmacie"],
                telephone=data["telephone"],
                adresse=data["adresse"],
                gouvernorat=data["gouvernorat"],
                url=data["url"],
            )
            db.add(pharmacien)
            test_users.append({"role": "Pharmacien", "email": data["email"], "password": data["password"]})
            print(f"  [OK] {data['nom']} --> {data['email']}")

        db.commit()

        # ------------------------------------------------------------------
        # Resume
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("[DONE] Utilisateurs de test crees avec succes !")
        print("=" * 60)
        print(f"\n{'ROLE':<25} {'EMAIL':<40} MOT DE PASSE")
        print("-" * 80)
        print(f"  {'Admin':<23} {'admin@avalive.tn':<40} Admin@2025")
        for u in test_users:
            print(f"  {u['role']:<23} {u['email']:<40} {u['password']}")

        print("\n[INFO] Les delegues existants (aziz, samar, ines @avalive.fr) sont deja dans la base.")
        print("[INFO] Leur mot de passe par defaut est celui qui etait dans la table delegates.")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] : {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
