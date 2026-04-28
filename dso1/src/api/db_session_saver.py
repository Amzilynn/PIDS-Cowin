"""
db_session_saver.py
─────────────────────────────────────────────────────────────────────────────
Persiste toutes les données d'une simulation dans la base de données SQL.

Tables alimentées :
  simulations  → méta-données session (délégué, produit, scores, durée)
  messages     → transcription complète (user + avatar)
  evaluations  → métriques CV + NLP

Appelé depuis session_manager._run_conversation() en toute fin de session.
─────────────────────────────────────────────────────────────────────────────
"""

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
    """Convertit proprement un float/str en Decimal pour SQLAlchemy."""
    if value is None:
        return default
    try:
        d = Decimal(str(round(float(value), 2)))
        # Clamp entre 0.00 et 1.00 pour les scores normalisés
        if d < 0:
            d = Decimal("0.00")
        if d > 1:
            d = Decimal("1.00")
        return d
    except (InvalidOperation, TypeError, ValueError):
        return default


def _to_decimal_score(value, default=None):
    """Convertit un score 0-100 en Decimal 0-100 (pour final_score)."""
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
    """
    Enregistre une simulation complète dans la base de données.

    Paramètres
    ----------
    delegue     : dict { id, nom, level, score, role }
    product     : dict { id, name, indications, ... } ou None
    messages    : list de dict { role, content }
    cv_summary  : dict retourné par session_logger.close() + nlp_report injecté
    start_time  : datetime du début de session (optionnel)

    Retourne le simulation_id créé, ou None en cas d'erreur.
    """
    db = SessionLocal()
    simulation_id = None

    try:
        # ── 1. Vérifier que le délégué existe dans la table delegates ──────────
        delegate_id = delegue.get("id")
        if not delegate_id:
            print("[DB Save] ERREUR: delegue sans ID, simulation non sauvegardée.")
            return None

        delegate_obj = db.query(Delegate).filter(Delegate.id == delegate_id).first()
        if not delegate_obj:
            print(f"[DB Save] ERREUR: Delegate ID {delegate_id} introuvable en base.")
            return None

        product_id = product.get("id") if product else None
        if not product_id:
            print("[DB Save] WARN: Aucun produit sélectionné, simulation sans product_id.")
            # On peut quand même sauvegarder mais sans lien produit (FK contrainte → skip)
            return None

        # ── 2. Créer la ligne Simulation ───────────────────────────────────────
        averages = cv_summary.get("averages", {}) if cv_summary else {}
        perf_score = averages.get("performance", 0.0)
        final_score_val = _to_decimal_score(perf_score * 100)  # Convertir 0-1 → 0-100

        sim = Simulation(
            delegate_id = delegate_id,
            product_id  = product_id,
            start_time  = start_time or datetime.utcnow(),
            end_time    = datetime.utcnow(),
            final_score = final_score_val,
        )
        db.add(sim)
        db.flush()  # Récupère sim.id sans commit
        simulation_id = sim.id
        print(f"[DB Save] Simulation #{simulation_id} créée (délégué={delegate_id}, produit={product_id})")

        # ── 3. Insérer les Messages (transcription) ────────────────────────────
        message_count = 0
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "").strip()

            # Ignorer messages système et mots-clés de contrôle
            if role not in ("user", "assistant"):
                continue
            if content.lower() in ["stop", "fin", "terminer", "quitter", "annuler", ""]:
                continue

            sender = "User" if role == "user" else "Avatar"
            msg_obj = Message(
                simulation_id = simulation_id,
                sender_type   = sender,
                content       = content,
            )
            db.add(msg_obj)
            message_count += 1

        print(f"[DB Save] {message_count} message(s) insérés.")

        # ── 4. Insérer l'Évaluation (CV + NLP) ────────────────────────────────
        nlp = cv_summary.get("nlp", {}) if cv_summary else {}

        # Métriques comportementales (CV)
        eval_obj = Evaluation(
            simulation_id          = simulation_id,
            confidence_score       = _to_decimal(averages.get("confidence")),
            stress_score           = _to_decimal(averages.get("stress")),
            engagement_score       = _to_decimal(averages.get("engagement")),
            posture_score          = _to_decimal(
                cv_summary.get("body_averages", {}).get("posture") if cv_summary else None
            ),
            eye_contact_rate       = _to_decimal(
                cv_summary.get("eye_contact_rate") if cv_summary else None
            ),
            dominant_emotion       = cv_summary.get("dominant_emotion") if cv_summary else None,
            dominant_tone          = cv_summary.get("dominant_tone") if cv_summary else None,

            # Métriques NLP
            product_knowledge_score = _to_decimal(nlp.get("product_knowledge_score")),
            vocabulary_richness     = _to_decimal(nlp.get("vocabulary_richness")),

            # Feedback textuel NLP
            feedback_summary        = nlp.get("feedback_summary"),

            # Erreurs et points validés (stockés en JSON)
            improvement_areas       = {
                "mistakes":       nlp.get("mistakes", []),
                "correct_points": nlp.get("correct_points", []),
                "grade":          cv_summary.get("grade") if cv_summary else None,
            },
        )
        db.add(eval_obj)
        print("[DB Save] Évaluation insérée (CV + NLP).")

        # ── 5. Incrémenter le compteur de simulations du délégué ───────────────
        delegate_obj.total_simulations_completed = (
            (delegate_obj.total_simulations_completed or 0) + 1
        )

        # ── 6. Commit final ────────────────────────────────────────────────────
        db.commit()
        print(f"[DB Save] ✅ Simulation #{simulation_id} persistée avec succès.")
        return simulation_id

    except Exception as e:
        db.rollback()
        print(f"[DB Save] ❌ ERREUR lors de la sauvegarde : {e}")
        traceback.print_exc()
        return None

    finally:
        db.close()
def update_simulation_report_path(simulation_id: int, report_path: str):
    """Met à jour le chemin du rapport pour une simulation existante."""
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
        if sim:
            sim.report_path = report_path
            db.commit()
            print(f"[DB Update] Report path updated for Simulation #{simulation_id}")
    except Exception as e:
        db.rollback()
        print(f"[DB Update] ❌ ERREUR: {e}")
    finally:
        db.close()
