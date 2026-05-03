"""
Route d'authentification : POST /api/auth/login
Reçoit email + password, retourne un JWT avec {user_id, type, sub_role}
"""

import os
import sys
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session

# Ajout du chemin src pour trouver les modules partagés
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..", "..")       # → dso1/src
ROOT_DIR = os.path.join(SRC_DIR, "..", "..")       # → racine du projet
sys.path.insert(0, ROOT_DIR)

from shared.database import get_db
from shared import models

# ─── Configuration JWT ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", "avalive_secret_key_change_in_prod_2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 heures

# ─── Contexte de hachage ──────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


# ─── Schémas Pydantic ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    type: str          # "delegue" | "medecin" | "pharmacien" | "admin"
    sub_role: str      # "medical" | "commercial" | "doctor" | "pharmacist" | "admin"
    display_name: str  # Nom affiché dans l'interface
    redirect_to: str   # Route React cible après login
    new_recommendations_count: int = 0
    new_recommendations: List[dict] = []


# ─── Helpers ──────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_display_name(user: models.User) -> str:
    """Retourne le nom affiché selon le type d'utilisateur."""
    if isinstance(user, models.Delegate):
        return f"{user.first_name} {user.last_name}"
    elif isinstance(user, models.Medecin):
        return f"Dr. {user.prenom} {user.nom}"
    elif isinstance(user, models.Pharmacien):
        return user.nom
    elif isinstance(user, models.Admin):
        return user.display_name or "Administrateur"
    return user.email


def get_sub_role_and_redirect(user: models.User) -> tuple[str, str]:
    """
    Retourne (sub_role, redirect_to) selon le type et sous-type de l'utilisateur.
    sub_role est utilisé par React pour choisir le bon layout.
    """
    if isinstance(user, models.Admin):
        return "admin", "/admin/dashboard"

    elif isinstance(user, models.Delegate):
        # role = "Medical" ou "Commercial"
        sub = "medical" if user.role == "Medical" else "commercial"
        return sub, f"/delegate/home?sub={sub}"

    elif isinstance(user, models.Medecin):
        return "doctor", "/practitioner/presentations?sub=doctor"

    elif isinstance(user, models.Pharmacien):
        return "pharmacist", "/practitioner/presentations?sub=pharmacist"

    return "unknown", "/"


# ─── Endpoint principal ───────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse, summary="Authentification utilisateur")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authentifie un utilisateur par email + mot de passe.
    Retourne un JWT et les informations de redirection selon le rôle.
    """
    # 1. Chercher l'utilisateur par email (table parente users)
    user = db.query(models.User).filter(
        models.User.email == payload.email.strip().lower()
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    # 2. Vérifier le mot de passe
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    # 3. Vérifier que le compte est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez l'administrateur.",
        )

    # 4. Mettre à jour last_login et vérifier les recommandations (DSO3)
    user.last_login = datetime.utcnow()
    
    # Logique de recommandation DSO3 intégrée
    previews = []
    if user.type == "delegue":
        from sqlalchemy import and_
        # On vérifie si de nouvelles recommandations existent depuis le dernier login
        rows = (
            db.query(models.Recommendation, models.Product)
            .join(models.Product, models.Product.id == models.Recommendation.product_id)
            .filter(
                and_(
                    models.Recommendation.delegate_id == user.id,
                    models.Recommendation.id > user.last_seen_recommendation_id
                )
            )
            .limit(5)
            .all()
        )
        
        max_id = user.last_seen_recommendation_id
        for rec, prod in rows:
            max_id = max(max_id, rec.id)
            previews.append({
                "recommendation_id": rec.id,
                "product_id": prod.id,
                "product_name": prod.name,
                "category": prod.category,
                "gamme_name": prod.gamme.name if prod.gamme else None,
                "score": float(rec.score)
            })
        
        if max_id > user.last_seen_recommendation_id:
            user.last_seen_recommendation_id = max_id
    
    db.commit()

    # 5. Calculer sub_role et redirect
    sub_role, redirect_to = get_sub_role_and_redirect(user)
    display_name = get_display_name(user)

    # 6. Créer le JWT
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "type": user.type,
        "sub_role": sub_role,
    }
    access_token = create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        type=user.type,
        sub_role=sub_role,
        display_name=display_name,
        redirect_to=redirect_to,
        new_recommendations_count=len(previews),
        new_recommendations=previews
    )


@router.get("/me", summary="Informations de l'utilisateur connecté")
def get_me(token: str, db: Session = Depends(get_db)):
    """
    Décode un JWT et retourne les informations de l'utilisateur connecté.
    Utile pour vérifier la session depuis React.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    sub_role, redirect_to = get_sub_role_and_redirect(user)
    return {
        "user_id": user.id,
        "email": user.email,
        "type": user.type,
        "sub_role": sub_role,
        "display_name": get_display_name(user),
        "redirect_to": redirect_to,
    }
