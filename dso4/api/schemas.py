"""Pydantic schemas for DSO4 API request/response models."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─── Request Models ──────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    """Request to optimize a delegate's route."""
    delegue_id: int
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    max_visits: int = Field(default=8, ge=1, le=20)
    radius_km: float = Field(default=20.0, ge=1.0, le=100.0)


class VisiteStatusUpdate(BaseModel):
    """Update a visit's status."""
    statut: str = Field(..., pattern="^(effectuee|annulee|reportee|planifiee)$")


class NearbyRequest(BaseModel):
    """Request for nearby doctors."""
    lat: float
    lng: float
    radius_km: float = Field(default=10.0, ge=0.5, le=50.0)
    limit: int = Field(default=20, ge=1, le=100)


# ─── Response Models ─────────────────────────────────────────────

class MedecinResponse(BaseModel):
    """Doctor info returned by the API."""
    id: int
    nom: str
    prenom: str
    specialite: str
    adresse: str = ""
    latitude: float
    longitude: float
    distance_km: Optional[float] = None


class DelegueResponse(BaseModel):
    """Delegate info."""
    id: int
    nom: str
    prenom: str
    email: str
    zone: str
    ville: str
    latitude: float
    longitude: float
    disponibilite: str


class ScheduleBlock(BaseModel):
    """A single time block in the schedule."""
    type: str  # "visite", "trajet", "pause", "overflow"
    start: str
    end: str
    duration_min: int
    description: Optional[str] = None
    visit_type: Optional[str] = None
    medecin_id: Optional[int] = None
    medecin_nom: Optional[str] = None
    specialite: Optional[str] = None
    adresse: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    travel_distance_km: Optional[float] = None
    statut: str = "planifiee"


class TourneeResponse(BaseModel):
    """Full day schedule for a delegate."""
    date: str
    delegate: str
    work_start: str
    work_end: str
    visits_scheduled: int
    total_visits: int
    total_travel_min: float
    total_visit_time_min: int
    efficiency_pct: float
    total_distance_km: float = 0.0
    blocks: List[ScheduleBlock]
    predictions: Optional[List[dict]] = None


class StatsResponse(BaseModel):
    """Performance stats for a delegate."""
    delegue_id: int
    delegue_nom: str
    total_visites: int
    visites_effectuees: int
    visites_annulees: int
    taux_realisation: float
    distance_totale_km: float
    score_moyen: float
    visites_physiques: int
    visites_en_ligne: int
    zones_couvertes: List[str] = []
