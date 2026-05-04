"""
DSO4 API Routes — Visit Strategy Optimizer endpoints.

All routes are prefixed with /api/tournee by the router.
Mounted into the shared DSO2 FastAPI app.

Data source: MySQL (avalive_dso4) via SQLAlchemy ORM.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import DSO4 models and shared DB (PROJECT_ROOT handles all paths)
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dso4.models.optimizer import optimize_route, optimize_route_realtime, calculate_total_distance, haversine
from dso4.models.scheduler import build_schedule
from dso4.models.realtime import get_weather
from dso4.api.schemas import (
    TourneeResponse, ScheduleBlock, StatsResponse,
    MedecinResponse, DelegueResponse, VisiteStatusUpdate,
    OptimizeRequest, WeatherResponse,
)

from shared.database import get_db
from shared.models import Delegate, Medecin, Pharmacien, Visit

router = APIRouter(prefix="/api/tournee", tags=["DSO4 - Visit Strategy"])


# ─── DB Helper Functions ──────────────────────────────────────────

def _get_delegate(delegue_id: int, db: Session):
    """Find a delegate by ID from MySQL."""
    return db.query(Delegate).filter(Delegate.id == delegue_id).first()


def _get_nearby_clients(lat: float, lng: float, radius_km: float, db: Session, client_type: str = "medecins", limit: int = 20):
    """Get doctors or pharmacies within radius of a point, from MySQL.
    Both use real GPS coordinates stored in the database.
    """
    nearby = []

    if client_type == "pharmacies":
        # Query only pharmacies that have real GPS coordinates
        rows = db.query(Pharmacien).filter(
            Pharmacien.latitude.isnot(None),
            Pharmacien.longitude.isnot(None),
        ).all()

        for r in rows:
            try:
                p_lat = float(r.latitude)
                p_lng = float(r.longitude)

                # Validate within Tunisia bounding box
                if not (30 < p_lat < 38 and 7 < p_lng < 12):
                    continue

                dist = haversine(lat, lng, p_lat, p_lng)
                if dist <= radius_km:
                    nearby.append({
                        "id": r.id,
                        "nom": r.nom,
                        "prenom": "",
                        "specialite": "Pharmacie",
                        "adresse": r.adresse or "",
                        "latitude": p_lat,
                        "longitude": p_lng,
                        "distance_km": round(dist, 2),
                    })
            except Exception:
                continue

    else:
        # Query doctors that have real GPS coordinates
        rows = db.query(Medecin).filter(
            Medecin.latitude.isnot(None),
            Medecin.longitude.isnot(None),
        ).all()

        for r in rows:
            try:
                m_lat = float(r.latitude)
                m_lng = float(r.longitude)

                # Validate within Tunisia bounding box
                if not (30 < m_lat < 38 and 7 < m_lng < 12):
                    continue

                dist = haversine(lat, lng, m_lat, m_lng)
                if dist <= radius_km:
                    nearby.append({
                        "id": r.id,
                        "nom": r.nom,
                        "prenom": r.prenom or "",
                        "specialite": r.specialite or "",
                        "adresse": r.adresse or "",
                        "latitude": m_lat,
                        "longitude": m_lng,
                        "distance_km": round(dist, 2),
                    })
            except Exception:
                continue

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby[:limit]


def _get_delegate_visits(delegue_id: int, db: Session):
    """Get all visits for a delegate from MySQL."""
    return db.query(Visit).filter(Visit.delegate_id == delegue_id).all()


def _filter_recent_visits(doctors, delegue_id: int, db: Session, days: int = 14):
    """Filter out doctors visited recently (within N days)."""
    cutoff = (datetime.now() - timedelta(days=days)).date()

    recent_ids = set(
        v.medecin_id
        for v in db.query(Visit).filter(
            Visit.delegate_id == delegue_id,
            Visit.date >= cutoff,
            Visit.status == "Effectuée",
        ).all()
    )

    filtered = [d for d in doctors if int(d.get("id")) not in recent_ids]
    return filtered if len(filtered) >= 8 else doctors


# ─── Endpoints ────────────────────────────────────────────────────

@router.get(
    "/{delegue_id}/today",
    response_model=TourneeResponse,
    summary="Get today's optimized schedule (real-time TomTom + weather)",
)
async def get_today_schedule(
    delegue_id: int,
    max_visits: int = Query(8, ge=1, le=20),
    target: str = Query("medecins"),
    db: Session = Depends(get_db),
):
    """Return today's optimized visit schedule using real road data and live weather."""
    delegate = _get_delegate(delegue_id, db)
    if not delegate:
        raise HTTPException(status_code=404, detail=f"Delegue {delegue_id} not found")

    d_lat = float(delegate.latitude)
    d_lng = float(delegate.longitude)
    d_name = f"{delegate.first_name} {delegate.last_name}"

    # Find nearby clients (doctors or pharmacies) using real GPS
    nearby_docs = _get_nearby_clients(d_lat, d_lng, radius_km=20, db=db, client_type=target, limit=max_visits * 2)

    if not nearby_docs:
        raise HTTPException(status_code=404, detail="No clients found near delegate zone")

    # Filter recently visited doctors to ensure variety
    selected = nearby_docs[:max_visits * 3]
    selected = _filter_recent_visits(selected, delegue_id, db=db, days=14)
    selected = selected[:max_visits]

    for doc in selected:
        doc["type_visite"] = "physique"
        doc["duree_min"] = 30

    # Real-time optimization: OR-Tools TSP + TomTom + Open-Meteo weather
    optimized, weather_info = await optimize_route_realtime(d_lat, d_lng, selected)

    schedule = build_schedule(
        optimized_visits=optimized,
        delegate_name=d_name,
    )

    total_dist = calculate_total_distance(optimized)

    blocks = []
    for b in schedule["blocks"]:
        blocks.append(ScheduleBlock(
            type=b["type"],
            start=b["start"],
            end=b["end"],
            duration_min=b.get("duration_min", 0),
            description=b.get("description"),
            visit_type=b.get("visit_type"),
            medecin_id=b.get("medecin_id"),
            medecin_nom=b.get("medecin_nom"),
            specialite=b.get("specialite"),
            adresse=b.get("adresse"),
            latitude=b.get("latitude"),
            longitude=b.get("longitude"),
            distance_km=b.get("distance_km"),
            travel_distance_km=b.get("travel_distance_km"),
            travel_time_min=b.get("travel_time_min"),
            travel_source=b.get("travel_source"),
            weather_override=b.get("weather_override", False),
            weather_reason=b.get("weather_reason"),
            statut="planifiee",
        ))

    weather_resp = WeatherResponse(
        rain_mm=weather_info.get("rain_mm", 0),
        wind_kmh=weather_info.get("wind_kmh", 0),
        weather_code=weather_info.get("weather_code", 0),
        condition=weather_info.get("condition", "unknown"),
        visit_recommendation=weather_info.get("visit_recommendation", "physique"),
        description=weather_info.get("description", ""),
    )

    return TourneeResponse(
        date=schedule["date"],
        delegate=schedule["delegate"],
        work_start=schedule["work_start"],
        work_end=schedule["work_end"],
        visits_scheduled=schedule["visits_scheduled"],
        total_visits=schedule["total_visits"],
        total_travel_min=schedule["total_travel_min"],
        total_visit_time_min=schedule["total_visit_time_min"],
        efficiency_pct=schedule["efficiency_pct"],
        total_distance_km=total_dist,
        blocks=blocks,
        predictions=[],
        weather=weather_resp,
    )


@router.get(
    "/{delegue_id}/optimize",
    response_model=TourneeResponse,
    summary="Re-run the real-time optimizer with fresh data",
)
async def optimize_schedule(
    delegue_id: int,
    max_visits: int = Query(8, ge=1, le=20),
    radius_km: float = Query(20.0, ge=1.0, le=100.0),
    target: str = Query("medecins"),
    db: Session = Depends(get_db),
):
    """Re-run the route optimizer with live TomTom + weather data."""
    return await get_today_schedule(delegue_id, max_visits, target, db)


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Get live weather at coordinates",
)
async def get_live_weather(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Return current weather conditions from Open-Meteo."""
    weather = await get_weather(lat, lng)
    return WeatherResponse(
        rain_mm=weather.get("rain_mm", 0),
        wind_kmh=weather.get("wind_kmh", 0),
        weather_code=weather.get("weather_code", 0),
        condition=weather.get("condition", "unknown"),
        visit_recommendation=weather.get("visit_recommendation", "physique"),
        description=weather.get("description", ""),
    )


@router.post(
    "/visite/{visite_id}/statut",
    summary="Update visit status",
)
async def update_visit_status(
    visite_id: int,
    body: VisiteStatusUpdate,
    db: Session = Depends(get_db),
):
    """Mark a visit as Effectuée, Annulée, or Reportée in MySQL."""
    visite = db.query(Visit).filter(Visit.id == visite_id).first()
    if not visite:
        raise HTTPException(status_code=404, detail=f"Visit {visite_id} not found")

    visite.status = body.statut.capitalize()
    db.commit()

    return {"message": f"Visit {visite_id} updated to {body.statut}", "visite_id": visite_id}


@router.get(
    "/medecins/nearby",
    response_model=list[MedecinResponse],
    summary="Find doctors near coordinates",
)
async def get_nearby_medecins(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(10.0, ge=0.5, le=50.0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return doctors within a given radius of coordinates."""
    docs = _get_nearby_clients(lat, lng, radius_km=radius, db=db, client_type="medecins", limit=limit)

    return [
        MedecinResponse(
            id=int(d.get("id", 0)),
            nom=d.get("nom", ""),
            prenom=d.get("prenom", ""),
            specialite=d.get("specialite", ""),
            adresse=d.get("adresse", ""),
            latitude=float(d.get("latitude", 0)),
            longitude=float(d.get("longitude", 0)),
            distance_km=d.get("distance_km"),
        )
        for d in docs
    ]


@router.get(
    "/delegues",
    response_model=list[DelegueResponse],
    summary="List all delegates",
)
async def list_delegues(db: Session = Depends(get_db)):
    """Return all delegates from MySQL."""
    rows = db.query(Delegate).all()
    return [
        DelegueResponse(
            id=r.id,
            nom=r.last_name,
            prenom=r.first_name,
            email=r.email,
            zone=r.address or "",
            ville=r.address or "",
            latitude=float(r.latitude) if r.latitude else 0.0,
            longitude=float(r.longitude) if r.longitude else 0.0,
            disponibilite="Lun-Ven",
        )
        for r in rows
    ]


@router.get(
    "/stats/{delegue_id}",
    response_model=StatsResponse,
    summary="Get delegate performance stats",
)
async def get_delegate_stats(
    delegue_id: int,
    db: Session = Depends(get_db),
):
    """Return performance statistics for a delegate from MySQL."""
    delegate = _get_delegate(delegue_id, db)
    if not delegate:
        raise HTTPException(status_code=404, detail=f"Delegue {delegue_id} not found")

    visits = _get_delegate_visits(delegue_id, db)

    effectuees = [v for v in visits if v.status == "Effectuée"]
    annulees   = [v for v in visits if v.status == "Annulée"]
    physiques  = [v for v in effectuees if v.visit_type == "Physique"]
    en_ligne   = [v for v in effectuees if v.visit_type == "En ligne"]

    total = len(visits)
    taux = round((len(effectuees) / total * 100), 1) if total > 0 else 0.0

    scores = [float(v.score_visite) for v in effectuees if v.score_visite and float(v.score_visite) > 0]
    score_moyen = round(sum(scores) / len(scores), 1) if scores else 0.0

    distances = [float(v.distance_km) for v in visits if v.distance_km]
    dist_total = round(sum(distances), 1)

    return StatsResponse(
        delegue_id=delegue_id,
        delegue_nom=f"{delegate.first_name} {delegate.last_name}",
        total_visites=total,
        visites_effectuees=len(effectuees),
        visites_annulees=len(annulees),
        taux_realisation_pct=taux,
        distance_totale_km=dist_total,
        score_moyen=score_moyen,
        visites_physiques=len(physiques),
        visites_en_ligne=len(en_ligne),
        zones_couvertes=[delegate.address or ""],
    )


@router.get("/health", summary="DSO4 health check")
async def dso4_health(db: Session = Depends(get_db)):
    """Check DSO4 module health including DB connectivity."""
    try:
        delegue_count  = db.query(func.count(Delegate.id)).scalar()
        medecin_count  = db.query(func.count(Medecin.id)).scalar()
        pharmacie_count = db.query(func.count(Pharmacien.id)).scalar()
        db_status = "connected"
    except Exception as e:
        delegue_count = medecin_count = pharmacie_count = 0
        db_status = f"error: {e}"

    return {
        "module": "dso4",
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "realtime_services": {
            "routing": "TomTom Routing API (live traffic)",
            "weather": "api.open-meteo.com (free, no key)",
        },
        "datasets": {
            "delegues":   delegue_count,
            "medecins":   medecin_count,
            "pharmacies": pharmacie_count,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }