"""
DSO4 — SQLAlchemy ORM Models for the Visit Strategy Optimizer.

Tables:
  • delegues_dso4       — Pharmaceutical delegates (medical & commercial)
  • medecins_dso4       — Doctors / physicians sourced from medecins.csv
  • pharmaciens_dso4    — Pharmacies sourced from pharmacies.csv
  • visites_dso4        — Historical visit records between delegates and doctors
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, Time,
    Numeric, Enum, ForeignKey, TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


# =============================================================================
# TABLE : Delegue (Délégué pharmaceutique)
# Source : dso4/data/delegues.csv
# Colonnes CSV : id, nom, prenom, email, zone, ville, latitude, longitude,
#                disponibilite
# =============================================================================

class DelegueDSO4(Base):
    __tablename__ = "delegues_dso4"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    prenom = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    zone = Column(String(100), nullable=True)
    ville = Column(String(150), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    disponibilite = Column(String(50), nullable=True)   # e.g. "Lun-Ven"
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship: a delegate has many visits
    visites = relationship("VisiteDSO4", back_populates="delegue")


# =============================================================================
# TABLE : Medecin (Médecin / Docteur)
# Source : dso2/data/raw/medecins.csv
# Colonnes CSV : id, nom, prenom, specialite, telephone, email, adresse,
#                latitude, longitude
# =============================================================================

class MedecinDSO4(Base):
    __tablename__ = "medecins_dso4"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    prenom = Column(String(150), nullable=True)
    specialite = Column(String(150), nullable=True)
    telephone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    adresse = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship: a doctor has many visits
    visites = relationship("VisiteDSO4", back_populates="medecin")


# =============================================================================
# TABLE : Pharmacien (Pharmacie)
# Source : dso2/data/raw/pharmacies.csv
# Colonnes CSV : id, nom, type, telephone, adresse, gouvernorat, url
# =============================================================================

class PharmacienDSO4(Base):
    __tablename__ = "pharmaciens_dso4"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    type_pharmacie = Column(
        Enum("jour", "nuit", name="type_pharmacie_enum"),
        nullable=True,
        default="jour",
    )
    telephone = Column(String(30), nullable=True)
    adresse = Column(String(500), nullable=True)
    gouvernorat = Column(String(100), nullable=True)
    url = Column(String(512), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


# =============================================================================
# TABLE : Visite (Historique des visites)
# Source : dso4/data/visites.csv
# Colonnes CSV : id, delegue_id, medecin_id, date, heure, duree_min, statut,
#                type_visite, score_visite, distance_km, specialite_medecin
# =============================================================================

class VisiteDSO4(Base):
    __tablename__ = "visites_dso4"

    id = Column(Integer, primary_key=True, index=True)
    delegue_id = Column(
        Integer,
        ForeignKey("delegues_dso4.id"),
        nullable=False,
        index=True,
    )
    medecin_id = Column(
        Integer,
        ForeignKey("medecins_dso4.id"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False)
    heure = Column(String(10), nullable=True)       # stored as "HH:MM"
    duree_min = Column(Integer, nullable=True)
    statut = Column(
        Enum("effectuée", "annulée", "reportée", "planifiee",
             name="statut_visite_enum"),
        nullable=False,
        default="planifiee",
    )
    type_visite = Column(
        Enum("physique", "en_ligne", name="type_visite_enum"),
        nullable=False,
        default="physique",
    )
    score_visite = Column(Numeric(4, 2), nullable=True)
    distance_km = Column(Float, nullable=True)
    specialite_medecin = Column(String(150), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    delegue = relationship("DelegueDSO4", back_populates="visites")
    medecin = relationship("MedecinDSO4", back_populates="visites")
