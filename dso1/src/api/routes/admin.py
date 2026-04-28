from fastapi import APIRouter, HTTPException
from shared.database import SessionLocal
from shared.models import Medecin, Pharmacien, Delegate, Simulation, User
from sqlalchemy import func

router = APIRouter()

@router.get("/medecins")
def get_medecins():
    db = SessionLocal()
    try:
        medecins = db.query(Medecin).all()
        return [
            {
                "id": m.id,
                "nom": m.nom,
                "prenom": m.prenom,
                "specialite": m.specialite,
                "telephone": m.telephone,
                "adresse": m.adresse
            }
            for m in medecins
        ]
    finally:
        db.close()

@router.get("/pharmaciens")
def get_pharmaciens():
    db = SessionLocal()
    try:
        pharmaciens = db.query(Pharmacien).all()
        return [
            {
                "id": p.id,
                "nom": p.nom,
                "type_pharmacie": p.type_pharmacie,
                "telephone": p.telephone,
                "adresse": p.adresse,
                "gouvernorat": p.gouvernorat
            }
            for p in pharmaciens
        ]
    finally:
        db.close()

@router.get("/delegues_summary")
def get_delegues_summary():
    db = SessionLocal()
    try:
        # On fait un group by par delegate_id pour compter les simulations
        sim_counts = db.query(
            Simulation.delegate_id, 
            func.count(Simulation.id).label("total_sims"),
            func.avg(Simulation.final_score).label("avg_score")
        ).group_by(Simulation.delegate_id).all()
        
        counts_map = {sc.delegate_id: {"count": sc.total_sims, "avg": sc.avg_score} for sc in sim_counts}
        
        delegues = db.query(Delegate).all()
        return [
            {
                "id": d.id,
                "nom": f"{d.first_name} {d.last_name}",
                "role": d.role,
                "level": d.current_level,
                "global_score": float(d.global_score),
                "total_sims_completed": counts_map.get(d.id, {}).get("count", 0),
                "actual_avg_score": float(counts_map.get(d.id, {}).get("avg", 0) or 0)
            }
            for d in delegues
        ]
    finally:
        db.close()

@router.get("/delegue_simulations/{delegue_id}")
def get_delegue_simulations(delegue_id: int):
    db = SessionLocal()
    try:
        sims = db.query(Simulation).filter(Simulation.delegate_id == delegue_id).order_by(Simulation.start_time.desc()).all()
        results = []
        for s in sims:
            try:
                results.append({
                    "id": s.id,
                    "product_name": s.product.name if s.product else "N/A",
                    "date": s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "N/A",
                    "score": float(s.final_score) if s.final_score else 0.0,
                    "report_path": s.report_path or "" 
                })
            except Exception as e:
                print(f"[Admin API] Erreur processing simulation {s.id}: {e}")
                continue
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
