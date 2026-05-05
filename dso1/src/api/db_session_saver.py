import os
import sys
import traceback
from datetime import datetime
from decimal import Decimal, InvalidOperation

# Résolution du chemin projet
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import SessionLocal
from shared.models import Simulation, Message, Evaluation, Delegate


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _to_decimal(value, default=None):
    if value is None:
        return default
    try:
        d = Decimal(str(round(float(value), 2)))
        if d < 0: d = Decimal("0.00")
        if d > 1: d = Decimal("1.00")
        return d
    except (InvalidOperation, TypeError, ValueError):
        return default


def _to_decimal_score(value, default=None):
    if value is None:
        return default
    try:
        return Decimal(str(round(float(value), 2)))
    except (InvalidOperation, TypeError, ValueError):
        return default


# ─── Sauvegarde principale ─────────────────────────────────────────────────────

def save_simulation_to_db(
    delegue: dict,
    product: dict,
    messages: list,
    cv_summary: dict,
    start_time: datetime = None,
) -> int | None:
    db = SessionLocal()
    simulation_id = None

    try:
        delegate_id = delegue.get("id")
        if not delegate_id:
            return None

        delegate_obj = db.query(Delegate).filter(Delegate.id == delegate_id).first()
        if not delegate_obj:
            return None

        product_id = product.get("id") if product else None
        if not product_id:
            return None

        averages = cv_summary.get("averages", {}) if cv_summary else {}
        perf_score = averages.get("performance", 0.0)
        final_score_val = _to_decimal_score(perf_score * 100)

        sim = Simulation(
            delegate_id = delegate_id,
            product_id  = product_id,
            start_time  = start_time or datetime.utcnow(),
            end_time    = datetime.utcnow(),
            final_score = final_score_val,
        )
        db.add(sim)
        db.flush()
        simulation_id = sim.id

        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "").strip()
            if role not in ("user", "assistant"): continue
            if content.lower() in ["stop", "fin", "terminer", "quitter", "annuler", ""]: continue

            sender = "User" if role == "user" else "Avatar"
            msg_obj = Message(
                simulation_id = simulation_id,
                sender_type   = sender,
                content       = content,
            )
            db.add(msg_obj)

        nlp = cv_summary.get("nlp", {}) if cv_summary else {}
        eval_obj = Evaluation(
            simulation_id          = simulation_id,
            confidence_score       = _to_decimal(averages.get("confidence")),
            stress_score           = _to_decimal(averages.get("stress")),
            engagement_score       = _to_decimal(averages.get("engagement")),
            posture_score          = _to_decimal(cv_summary.get("body_averages", {}).get("posture") if cv_summary else None),
            eye_contact_rate       = _to_decimal(cv_summary.get("eye_contact_rate") if cv_summary else None),
            dominant_emotion       = cv_summary.get("dominant_emotion") if cv_summary else None,
            dominant_tone          = cv_summary.get("dominant_tone") if cv_summary else None,
            product_knowledge_score = _to_decimal(nlp.get("product_knowledge_score")),
            vocabulary_richness     = _to_decimal(nlp.get("vocabulary_richness")),
            feedback_summary        = nlp.get("feedback_summary"),
            improvement_areas       = {
                "mistakes":       nlp.get("mistakes", []),
                "correct_points": nlp.get("correct_points", []),
                "grade":          cv_summary.get("grade") if cv_summary else None,
            },
        )
        db.add(eval_obj)

        delegate_obj.total_simulations_completed = (delegate_obj.total_simulations_completed or 0) + 1

        db.commit()

        # ── 7. Mise à jour Expertise DSO3 (RÉ-ACTIVÉ) ──────────────────────────
        try:
            from dso3.services.recommender import update_delegate_expertise
            update_delegate_expertise(db, delegate_id)
            print(f"[DSO3] Expertise mise à jour pour le délégué {delegate_id}")
        except Exception as e:
            print(f"[DSO3] Erreur mise à jour expertise: {e}")

        return simulation_id

    except Exception as e:
        db.rollback()
        traceback.print_exc()
        return None
    finally:
        db.close()

def update_simulation_report_path(simulation_id: int, report_path: str):
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
        if sim:
            sim.report_path = report_path
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
