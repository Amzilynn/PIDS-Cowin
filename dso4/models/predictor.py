"""
Visit Predictor — recommends physical vs online visits.

Trained on visites.csv history using a RandomForestClassifier.
Features: distance_km, score_visite, specialty (encoded), days_since_last_visit
Output : "physique" or "en_ligne" + confidence score
"""

import os
import csv
import pickle
import math
from typing import Dict, Tuple, Optional

# Try sklearn, fallback to rule-based if not available
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
MODEL_PATH = os.path.join(DATA_DIR, "predictor_model.pkl")
ENCODER_PATH = os.path.join(DATA_DIR, "specialite_encoder.pkl")


def load_csv(path: str):
    """Load CSV with BOM handling."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return list(csv.DictReader(f))


def train_model() -> Tuple:
    """
    Train the visit type predictor on visites.csv.
    Returns (model, label_encoder, accuracy) or (None, None, 0) if sklearn unavailable.
    """
    visites_path = os.path.join(DATA_DIR, "visites.csv")

    if not os.path.exists(visites_path):
        print(f"[predictor] visites.csv not found at {visites_path}")
        return None, None, 0.0

    rows = load_csv(visites_path)

    # Filter out cancelled visits (no useful signal)
    valid = [r for r in rows if r["statut"] != "annulee" and r["statut"] != "annulée"]

    if not valid:
        return None, None, 0.0

    if not HAS_SKLEARN:
        print("[predictor] scikit-learn not installed, using rule-based fallback")
        return None, None, 0.0

    # Encode specialties
    specialites = [r.get("specialite_medecin", "Inconnu") for r in valid]
    le = LabelEncoder()
    le.fit(specialites)

    # Build feature matrix
    X = []
    y = []
    for r in valid:
        try:
            distance = float(r.get("distance_km", 0))
            score = float(r.get("score_visite", 5))
            spec_encoded = le.transform([r.get("specialite_medecin", "Inconnu")])[0]
            duree = float(r.get("duree_min", 20))

            X.append([distance, score, spec_encoded, duree])
            y.append(1 if r["type_visite"] == "physique" else 0)
        except (ValueError, KeyError):
            continue

    if len(X) < 10:
        return None, None, 0.0

    # Train RandomForest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X, y)

    # Quick accuracy on training data (not ideal, but sufficient for this use case)
    accuracy = clf.score(X, y)

    # Save model and encoder
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(le, f)

    print(f"[predictor] Model trained: accuracy={accuracy:.2%}, samples={len(X)}")
    return clf, le, accuracy


def load_model() -> Tuple:
    """Load a previously trained model, or train a new one."""
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                clf = pickle.load(f)
            with open(ENCODER_PATH, "rb") as f:
                le = pickle.load(f)
            return clf, le
        except Exception:
            pass

    clf, le, _ = train_model()
    return clf, le


def predict_visit_type(
    distance_km: float,
    score_visite: float,
    specialite: str,
    duree_estimee: float = 25.0,
    model=None,
    encoder=None,
) -> Dict:
    """
    Predict whether a visit should be physical or online.

    Returns
    -------
    dict with keys: type_visite, confidence, reasoning
    """
    # If model available, use ML prediction
    if model is not None and encoder is not None and HAS_SKLEARN:
        try:
            spec_encoded = encoder.transform([specialite])[0]
        except (ValueError, KeyError):
            spec_encoded = 0

        features = [[distance_km, score_visite, spec_encoded, duree_estimee]]
        prediction = model.predict(features)[0]
        probas = model.predict_proba(features)[0]
        confidence = round(max(probas) * 100, 1)

        visit_type = "physique" if prediction == 1 else "en_ligne"

        return {
            "type_visite": visit_type,
            "confidence": confidence,
            "method": "ml_prediction",
            "reasoning": _build_reasoning(visit_type, distance_km, score_visite, confidence)
        }

    # Rule-based fallback
    return _rule_based_prediction(distance_km, score_visite, specialite)


def _rule_based_prediction(
    distance_km: float,
    score_visite: float,
    specialite: str,
) -> Dict:
    """Fallback rule-based prediction when sklearn isn't available."""
    score = 0.0

    # Distance factor: closer = more likely physical
    if distance_km <= 5:
        score += 0.4
    elif distance_km <= 10:
        score += 0.2
    elif distance_km <= 20:
        score -= 0.1
    else:
        score -= 0.3

    # Score factor: higher past scores = physical preference
    if score_visite >= 8:
        score += 0.3
    elif score_visite >= 6:
        score += 0.1
    else:
        score -= 0.1

    # Specialty factor: certain specialties prefer in-person
    in_person_specialties = [
        "Cardiologie", "Ophtalmologie", "Chirurgie",
        "Neurologie", "Oncologie", "Dermatologie"
    ]
    if any(s.lower() in specialite.lower() for s in in_person_specialties):
        score += 0.2

    visit_type = "physique" if score >= 0.2 else "en_ligne"
    confidence = round(min(95, max(55, 65 + score * 50)), 1)

    return {
        "type_visite": visit_type,
        "confidence": confidence,
        "method": "rule_based",
        "reasoning": _build_reasoning(visit_type, distance_km, score_visite, confidence)
    }


def _build_reasoning(
    visit_type: str,
    distance_km: float,
    score: float,
    confidence: float
) -> str:
    """Build a human-readable explanation for the prediction."""
    if visit_type == "physique":
        reasons = []
        if distance_km <= 10:
            reasons.append(f"proximite ({distance_km:.1f} km)")
        if score >= 7:
            reasons.append(f"score eleve ({score:.1f}/10)")
        reasons.append(f"confiance {confidence}%")
        return f"Visite physique recommandee: {', '.join(reasons)}"
    else:
        reasons = []
        if distance_km > 15:
            reasons.append(f"distance elevee ({distance_km:.1f} km)")
        if score < 6:
            reasons.append(f"score faible ({score:.1f}/10)")
        reasons.append(f"confiance {confidence}%")
        return f"Visite en ligne recommandee: {', '.join(reasons)}"
