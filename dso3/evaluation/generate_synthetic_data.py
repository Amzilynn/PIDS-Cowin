import csv
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from dso3.database import SessionLocal, Base, engine
from dso3.models.delegate import Delegate
from dso3.models.product import Product

def create_synthetic_data():
    Base.metadata.create_all(bind=engine)  # Ensure tables exist
    db = SessionLocal()

    try:
        # Clear existing synthetic data if needed (optional, keeping it simple for now)
        pass

        print("Génération de données synthétiques...")

        # 1. Création de produits fictifs
        products_data = [
            {"name": "CardioPlus", "category": "Cardiologie", "description": "Traitement de l'hypertension artérielle et insuffisance cardiaque."},
            {"name": "DermaHeal", "category": "Dermatologie", "description": "Crème apaisante pour les irritations cutanées chroniques, eczéma."},
            {"name": "NeuroCalm", "category": "Neurologie", "description": "Sédatif léger pour les troubles du sommeil et l'anxiété."},
            {"name": "GastroRelief", "category": "Gastro-entérologie", "description": "Pansement gastrique pour ulcères et reflux douloureux."},
            {"name": "PneumoBreathe", "category": "Pneumologie", "description": "Inhalateur pour le traitement de l'asthme bronchique."}
        ]

        products = []
        for p_data in products_data:
            # Check if exists
            p = db.query(Product).filter_by(name=p_data["name"]).first()
            if not p:
                p = Product(**p_data)
                db.add(p)
            products.append(p)
        db.commit()

        # 2. Création de délégués fictifs
        delegates_data = [
            {"user_id": 101, "name": "Alice Dupont", "expertise": "Cardiologie", "interests": "Maladies cardiaques, hypertension", "specification": "Spécialiste hôpital"},
            {"user_id": 102, "name": "Bob Martin", "expertise": "Dermatologie", "interests": "Soins de la peau, allergies", "specification": "Cliniques privées"},
            {"user_id": 103, "name": "Charlie R.", "expertise": "Neurologie", "interests": "Troubles nerveux, psychiatrie", "specification": "Centres médicaux"},
            {"user_id": 104, "name": "Diana L.", "expertise": "Gastro-entérologie", "interests": "Système digestif, nutrition", "specification": "Médecins généralistes"},
            {"user_id": 105, "name": "Eve C.", "expertise": "Pneumologie", "interests": "Maladies respiratoires, allergies", "specification": "Pneumologues"}
        ]

        delegates = []
        for d_data in delegates_data:
            # Check if exists
            d = db.query(Delegate).filter_by(name=d_data["name"]).first()
            if not d:
                d = Delegate(**d_data)
                db.add(d)
            delegates.append(d)
        db.commit()

        # Refresh objects to get IDs
        for p in products:
            db.refresh(p)
        for d in delegates:
            db.refresh(d)

        print(f"✅ {len(products)} produits et {len(delegates)} délégués générés/vérifiés dans la base de données.")

        # 3. Création du fichier CSV de vérité terrain (Ground Truth)
        csv_path = Path(__file__).parent / "synthetic_ground_truth.csv"
        
        # Mapping logique basé sur les catégories (Produit -> Délégué ayant la même expertise)
        ground_truth = []
        for p in products:
            matching_delegates = [str(d.id) for d in delegates if d.expertise == p.category]
            if matching_delegates:
                ground_truth.append({
                    "product_id": p.id,
                    "true_delegate_ids": ",".join(matching_delegates)
                })

        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["product_id", "true_delegate_ids"])
            writer.writeheader()
            for row in ground_truth:
                writer.writerow(row)

        print(f"✅ Fichier d'évaluation généré avec succès : {csv_path}")
        print("\nVous pouvez maintenant lancer l'évaluation avec cette commande :")
        print(f"python -m dso3.evaluation.recommender_metrics --csv {csv_path} --k 1")

    finally:
        db.close()

if __name__ == "__main__":
    create_synthetic_data()
