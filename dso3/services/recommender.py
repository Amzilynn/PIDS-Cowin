from shared.models import Simulation, Delegate, Product, Gamme, Notification
from sqlalchemy import case, func, desc

def recommend_delegates(db, product, limit=10):
    """
    Recommend delegates for a product based on:
    1. Their 'expertise' matching the product's Gamme name.
    2. Their average simulation scores in this same Gamme.
    """
    if not product or not product.gamme_id:
        return []

    # Get the target Gamme name
    target_gamme = db.query(Gamme).get(product.gamme_id)
    target_gamme_name = target_gamme.name if target_gamme else None

    # Query: We want ALL delegates (outer join with simulations)
    # to include those who haven't done a simulation yet but are experts.
    results = (
        db.query(
            Delegate.id.label("delegate_id"),
            Delegate.first_name,
            Delegate.last_name,
            Delegate.expertise,
            func.avg(Simulation.final_score).label("avg_score")
        )
        .outerjoin(Simulation, Simulation.delegate_id == Delegate.id)
        .outerjoin(Product, Simulation.product_id == Product.id)
        # Filter: We can't filter strictly by gamme_id in the join if we want all delegates,
        # but the user said "dans la gamme concerné".
        # So we calculate the score FOR that gamme if it exists.
        .group_by(Delegate.id)
        .order_by(
            # 1. Expertise match (1 if match, 0 otherwise)
            case((Delegate.expertise == target_gamme_name, 1), else_=0).desc(),
            # 2. Average score (desc)
            desc("avg_score")
        )
        .limit(limit)
        .all()
    )

    recommendations = []
    for r in results:
        # Score is the average in the database (or 0 if no simulations)
        score = float(r.avg_score) if r.avg_score is not None else 0.0
        
        recommendations.append({
            "delegate_id": r.delegate_id,
            "delegate_name": f"{r.first_name} {r.last_name}".strip(),
            "expertise": r.expertise or "Généraliste",
            "score": round(score, 2)
        })

    return recommendations

def update_delegate_expertise(db, delegate_id: int):
    """
    Utility function to update a delegate's expertise based on their best Gamme.
    This can be called asynchronously or after a simulation ends.
    """
    from shared.models import Gamme

    best_gamme = (
        db.query(
            Gamme.name,
            func.avg(Simulation.final_score).label("avg_score")
        )
        .join(Product, Product.gamme_id == Gamme.id)
        .join(Simulation, Simulation.product_id == Product.id)
        .filter(Simulation.delegate_id == delegate_id)
        .group_by(Gamme.id)
        .order_by(desc("avg_score"))
        .first()
    )

    if best_gamme:
        delegate = db.query(Delegate).filter(Delegate.id == delegate_id).first()
        if delegate:
            old_expertise = delegate.expertise
            delegate.expertise = best_gamme.name
            
            # Notification si l'expertise change
            if old_expertise != best_gamme.name:
                db.add(Notification(
                    user_id=delegate_id,
                    title="Expertise Mise à Jour",
                    message=f"Félicitations ! Suite à vos excellentes performances, votre expertise a été mise à jour en : {best_gamme.name}.",
                    type="system"
                ))
            
            db.commit()
