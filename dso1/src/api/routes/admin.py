from fastapi import APIRouter, HTTPException
from shared.database import SessionLocal
from shared.models import Medecin, Pharmacien, Delegate, Simulation, User, Product, Recommendation, Gamme
from sqlalchemy import func, desc, and_
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter()

@router.get("/medecins")
def get_medecins():
    db = SessionLocal()
    try:
        medecins = db.query(Medecin).all()
        return [{"id": m.id, "nom": m.nom, "prenom": m.prenom, "specialite": m.specialite, "telephone": m.telephone, "adresse": m.adresse} for m in medecins]
    finally:
        db.close()

@router.get("/pharmaciens")
def get_pharmaciens():
    db = SessionLocal()
    try:
        pharmaciens = db.query(Pharmacien).all()
        return [{"id": p.id, "nom": p.nom, "type_pharmacie": p.type_pharmacie, "telephone": p.telephone, "adresse": p.adresse, "gouvernorat": p.gouvernorat} for p in pharmaciens]
    finally:
        db.close()

@router.get("/delegues_summary")
def get_delegues_summary():
    db = SessionLocal()
    try:
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
                "expertise": d.expertise or "Non définie",
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
            results.append({
                "id": s.id,
                "product_name": s.product.name if s.product else "N/A",
                "date": s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "N/A",
                "score": float(s.final_score) if s.final_score else 0.0,
                "report_path": s.report_path or "" 
            })
        return results
    finally:
        db.close()

# --- DSO3 INTEGRATION ---

class ProductCreate(BaseModel):
    name: str
    gamme_id: int
    category: Optional[str] = None
    description: Optional[str] = None
    indications: Optional[str] = None
    compositions: Optional[str] = None
    usage_advice: Optional[str] = None

@router.post("/products/product")
def admin_create_product(product_data: ProductCreate):
    db = SessionLocal()
    try:
        new_product = Product(
            name=product_data.name,
            gamme_id=product_data.gamme_id,
            category=product_data.category,
            description=product_data.description,
            indications=product_data.indications,
            compositions=product_data.compositions,
            usage_advice=product_data.usage_advice
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        recs = []
        try:
            from dso3.services.recommender import recommend_delegates
            recs = recommend_delegates(db, new_product)
        except Exception as e:
            print(f"[Admin API] Recommendation error: {e}")

        return {"message": "Product created", "product_id": new_product.id, "recommendations": recs}
    finally:
        db.close()

class ConfirmRecommendationsRequest(BaseModel):
    product_id: int
    delegate_ids: List[int]

@router.post("/products/confirm-recommendations")
def confirm_recommendations(body: ConfirmRecommendationsRequest):
    db = SessionLocal()
    try:
        from dso3.services.recommender import recommend_delegates
        product = db.query(Product).get(body.product_id)
        if not product: raise HTTPException(status_code=404, detail="Product not found")
        all_recs = recommend_delegates(db, product)
        recs_map = {r["delegate_id"]: r["score"] for r in all_recs}
        for d_id in body.delegate_ids:
            score = recs_map.get(d_id, 0.0)
            db.add(Recommendation(product_id=product.id, delegate_id=d_id, score=score))
        db.commit()
        return {"message": f"{len(body.delegate_ids)} recommendations saved."}
    finally:
        db.close()

@router.get("/training/products")
def get_all_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [{"id": p.id, "name": p.name, "gamme_id": p.gamme_id, "description": p.description, "category": p.category} for p in products]
    finally:
        db.close()

@router.get("/training/gammes")
def get_all_gammes():
    db = SessionLocal()
    try:
        gammes = db.query(Gamme).all()
        return [{"id": g.id, "name": g.name} for g in gammes]
    finally:
        db.close()

@router.get("/products/affectations")
def get_recent_affectations():
    db = SessionLocal()
    try:
        affectations = (
            db.query(Recommendation, Product, Delegate)
            .join(Product, Recommendation.product_id == Product.id)
            .join(Delegate, Recommendation.delegate_id == Delegate.id)
            .order_by(Recommendation.created_at.desc())
            .limit(20).all()
        )
        return [{"id": rec.id, "delegate_name": f"{d.first_name} {d.last_name}", "product_name": p.name, "score": float(rec.score), "date": rec.created_at.strftime("%Y-%m-%d %H:%M")} for rec, p, d in affectations]
    finally:
        db.close()
