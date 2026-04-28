import os
import sys
from datetime import datetime

# Root resolution
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "dso1", "src"))

from shared.database import SessionLocal
from shared.models import Simulation, Message, Evaluation
from report_generator import generate_report
from sqlalchemy import or_

def run_regeneration():
    db = SessionLocal()
    reports_dir = os.path.join(PROJECT_ROOT, "dso1", "reports")
    try:
        # 1. On récupère TOUTES les simulations
        sims = db.query(Simulation).all()
        print(f"--- REGENERATION FORCEE DES RAPPORTS ({len(sims)} à traiter) ---")

        for sim in sims:
            print(f"\nTraitement Simulation #{sim.id} (Délégué: {sim.delegate.first_name})...")
            
            # 2. Récupérer les messages
            msgs = db.query(Message).filter(Message.simulation_id == sim.id).all()
            formatted_messages = [
                {"role": "user" if m.sender_type == "User" else "assistant", "content": m.content}
                for m in msgs
            ]
            
            # 3. Récupérer l'évaluation
            eval_data = db.query(Evaluation).filter(Evaluation.simulation_id == sim.id).first()
            cv_summary = {}
            if eval_data:
                cv_summary = {
                    "averages": {
                        "performance": float(sim.final_score)/100 if sim.final_score else 0,
                        "confidence": float(eval_data.confidence_score or 0),
                        "engagement": float(eval_data.engagement_score or 0),
                        "stress": float(eval_data.stress_score or 0)
                    },
                    "nlp": {
                        "feedback_summary": eval_data.feedback_summary or "",
                        "mistakes": eval_data.improvement_areas.get("mistakes", []) if eval_data.improvement_areas else [],
                        "correct_points": eval_data.improvement_areas.get("correct_points", []) if eval_data.improvement_areas else []
                    }
                }

            # 4. Générer le rapport
            delegue_info = {"nom": f"{sim.delegate.first_name} {sim.delegate.last_name}"}
            try:
                # On utilise une date fixe pour ne pas tromper le lecteur (date de la sim originale)
                report_path_full = generate_report(delegue_info, formatted_messages, cv_summary)
                
                if report_path_full:
                    # Extraire juste le nom du fichier
                    filename = os.path.basename(report_path_full)
                    sim.report_path = filename
                    db.commit()
                    print(f"  [OK] Rapport genere et lie : {filename}")
                else:
                    print(f"  [Error] Echec de generation pour #{sim.id}")
            except Exception as e:
                print(f"  [Error] Erreur lors du traitement de #{sim.id}: {e}")
                db.rollback()

    finally:
        db.close()
    print("\n--- FIN DE LA REGENERATION ---")

if __name__ == "__main__":
    run_regeneration()
