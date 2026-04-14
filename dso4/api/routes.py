"""
DSO4 API Routes — Visit Strategy Optimizer endpoints.

All routes are prefixed with /api/tournee by the router.
Mounted into the shared DSO2 FastAPI app.
"""

from __future__ import annotations

import os
import csv
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status

# Import DSO4 models
import sys
DSO4_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DSO4_ROOT)

from dso4.models.optimizer import optimize_route, optimize_route_realtime, calculate_total_distance, calculate_total_travel_time, haversine
from dso4.models.scheduler import build_schedule
from dso4.models.realtime import get_weather
from dso4.api.schemas import (
    TourneeResponse, ScheduleBlock, StatsResponse,
    MedecinResponse, DelegueResponse, VisiteStatusUpdate,
    OptimizeRequest, WeatherResponse,
)

router = APIRouter(prefix="/api/tournee", tags=["DSO4 - Visit Strategy"])

# ─── Data paths ──────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DSO4_DATA = os.path.join(PROJECT_ROOT, "dso4", "data")
DSO2_DATA = os.path.join(PROJECT_ROOT, "dso2", "data", "raw")

DELEGUES_PATH = os.path.join(DSO4_DATA, "delegues.csv")
VISITES_PATH = os.path.join(DSO4_DATA, "visites.csv")
MEDECINS_PATH = os.path.join(DSO2_DATA, "medecins.csv")


# ─── CSV Helpers ─────────────────────────────────────────────────

def _load_csv(path: str):
    """Load CSV with BOM handling."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def _get_delegate(delegue_id: int):
    """Find a delegate by ID."""
    rows = _load_csv(DELEGUES_PATH)
    for r in rows:
        if int(r["id"]) == delegue_id:
            return r
    return None


def _get_nearby_doctors(lat: float, lng: float, radius_km: float, limit: int = 20):
    """Get doctors within radius of a point."""
    rows = _load_csv(MEDECINS_PATH)
    nearby = []
    for r in rows:
        try:
            m_lat = float(r["latitude"])
            m_lng = float(r["longitude"])
            # Sanity check for Tunisian coords
            if not (30 < m_lat < 38 and 7 < m_lng < 12):
                continue
            dist = haversine(lat, lng, m_lat, m_lng)
            if dist <= radius_km:
                r["distance_km"] = round(dist, 2)
                nearby.append(r)
        except (ValueError, KeyError):
            continue
    nearby.sort(key=lambda x: x["distance_km"])
    return nearby[:limit]


def _get_delegate_visits(delegue_id: int):
    """Get all visits for a delegate from visites.csv."""
    rows = _load_csv(VISITES_PATH)
    return [r for r in rows if int(r.get("delegue_id", 0)) == delegue_id]


def _filter_recent_visits(doctors, delegue_id: int, days: int = 14):
    """Filter out doctors that were visited recently."""
    visits = _get_delegate_visits(delegue_id)
    cutoff = datetime.now() - timedelta(days=days)
    
    # IDs visited recently
    recent_ids = set()
    for v in visits:
        try:
            visit_date = datetime.strptime(v["date"], "%Y-%m-%d")
            # Usually we check if it's effectuee, but let's just stick to the basic check
            if visit_date >= cutoff and v.get("statut") in ("effectuee", "effectuée"):
                recent_ids.add(int(v["medecin_id"]))
        except (ValueError, KeyError):
            continue
    
    # Return only doctors not visited recently
    filtered = [d for d in doctors if int(d.get("id")) not in recent_ids]
    
    # Safety: if filter removes everything, return original list
    return filtered if len(filtered) >= 8 else doctors





# ─── Endpoints ───────────────────────────────────────────────────


@router.get(
    "/{delegue_id}/today",
    response_model=TourneeResponse,
    summary="Get today's optimized schedule (real-time OSRM + weather)",
)
async def get_today_schedule(delegue_id: int, max_visits: int = Query(8, ge=1, le=20)):
    """Return today's optimized visit schedule using real road data and live weather."""
    delegate = _get_delegate(delegue_id)
    if not delegate:
        raise HTTPException(status_code=404, detail=f"Delegue {delegue_id} not found")

    d_lat = float(delegate["latitude"])
    d_lng = float(delegate["longitude"])
    d_name = f"{delegate['prenom']} {delegate['nom']}"

    # Find nearby doctors to visit
    nearby_docs = _get_nearby_doctors(d_lat, d_lng, radius_km=20, limit=max_visits * 2)

    if not nearby_docs:
        raise HTTPException(status_code=404, detail="No doctors found near delegate zone")

    # Pick a subset for today's visits
    selected = nearby_docs[:max_visits*3]
    selected = _filter_recent_visits(selected, delegue_id, days=14)
    selected = selected[:max_visits]

    # Add visit info
    for doc in selected:
        doc["type_visite"] = "physique"
        doc["duree_min"] = 8

    # ── Real-time optimization (OSRM + weather) ──
    optimized, weather_info = await optimize_route_realtime(d_lat, d_lng, selected)

    # Build schedule from optimized route
    schedule = build_schedule(
        optimized_visits=optimized,
        delegate_name=d_name,
    )

    # Calculate total distance
    total_dist = calculate_total_distance(optimized)

    # Convert blocks to ScheduleBlock models
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

    # Build weather response
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
):
    """Re-run the route optimizer with live OSRM + weather data."""
    return await get_today_schedule(delegue_id, max_visits)


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Get live weather at coordinates",
)
async def get_live_weather(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Return current weather conditions from Open-Meteo (free, no key)."""
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
async def update_visit_status(visite_id: int, body: VisiteStatusUpdate):
    """Mark a visit as effectuee, annulee, or reportee."""
    rows = _load_csv(VISITES_PATH)
    found = False
    for r in rows:
        if int(r.get("id", 0)) == visite_id:
            r["statut"] = body.statut
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Visit {visite_id} not found")

    # Write back
    if rows:
        fieldnames = list(rows[0].keys())
        with open(VISITES_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

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
):
    """Return doctors within a given radius of coordinates."""
    docs = _get_nearby_doctors(lat, lng, radius, limit)

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
async def list_delegues():
    """Return all delegates."""
    rows = _load_csv(DELEGUES_PATH)
    return [
        DelegueResponse(
            id=int(r["id"]),
            nom=r["nom"],
            prenom=r["prenom"],
            email=r["email"],
            zone=r["zone"],
            ville=r["ville"],
            latitude=float(r["latitude"]),
            longitude=float(r["longitude"]),
            disponibilite=r["disponibilite"],
        )
        for r in rows
    ]


@router.get(
    "/stats/{delegue_id}",
    response_model=StatsResponse,
    summary="Get delegate performance stats",
)
async def get_delegate_stats(delegue_id: int):
    """Return performance statistics for a delegate."""
    delegate = _get_delegate(delegue_id)
    if not delegate:
        raise HTTPException(status_code=404, detail=f"Delegue {delegue_id} not found")

    visits = _get_delegate_visits(delegue_id)

    effectuees = [v for v in visits if v.get("statut") == "effectuee" or v.get("statut") == "effectuée"]
    annulees = [v for v in visits if v.get("statut") == "annulee" or v.get("statut") == "annulée"]
    physiques = [v for v in effectuees if v.get("type_visite") == "physique"]
    en_ligne = [v for v in effectuees if v.get("type_visite") == "en_ligne"]

    total = len(visits)
    taux = round((len(effectuees) / total * 100), 1) if total > 0 else 0.0

    scores = [float(v.get("score_visite", 0)) for v in effectuees if float(v.get("score_visite", 0)) > 0]
    score_moyen = round(sum(scores) / len(scores), 1) if scores else 0.0

    distances = [float(v.get("distance_km", 0)) for v in visits]
    dist_total = round(sum(distances), 1)

    return StatsResponse(
        delegue_id=delegue_id,
        delegue_nom=f"{delegate['prenom']} {delegate['nom']}",
        total_visites=total,
        visites_effectuees=len(effectuees),
        visites_annulees=len(annulees),
        taux_realisation=taux,
        distance_totale_km=dist_total,
        score_moyen=score_moyen,
        visites_physiques=len(physiques),
        visites_en_ligne=len(en_ligne),
        zones_couvertes=[delegate.get("zone", "")],
    )


@router.get("/health", summary="DSO4 health check")
async def dso4_health():
    """Check DSO4 module health."""
    has_delegues = os.path.exists(DELEGUES_PATH)
    has_visites = os.path.exists(VISITES_PATH)
    has_medecins = os.path.exists(MEDECINS_PATH)

    return {
        "module": "dso4",
        "status": "ok" if (has_delegues and has_medecins) else "degraded",
        "realtime_services": {
            "osrm": "router.project-osrm.org (free, no key)",
            "weather": "api.open-meteo.com (free, no key)",
        },
        "datasets": {
            "delegues": has_delegues,
            "visites": has_visites,
            "medecins": has_medecins,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
