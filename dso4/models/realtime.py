"""
Real-Time External Services — OSRM routing + Open-Meteo weather.

Both APIs are 100% free, no API key required.
- OSRM: real road distances and driving durations
- Open-Meteo: current weather (rain, wind) for visit-type decisions
"""

import math
import httpx

# ─── Timeout config ──────────────────────────────────────────────
OSRM_TIMEOUT = 8.0   # seconds
METEO_TIMEOUT = 5.0   # seconds


# ─── TomTom — Real Road Distance & Live Traffic ───────────────────────

TOMTOM_API_KEY = "BBZUyFODGVUTRMgdBYJ4hZByLfqnxPH3"
TOMTOM_TIMEOUT = 10.0

async def get_real_travel_time(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> dict | None:
    """
    Call the TomTom public routing API to get real road distance and
    driving duration between two GPS coordinates, factoring in live traffic delays.

    Returns
    -------
    dict with keys: distance_km, duration_min
    None if the API call fails (caller should fall back to Haversine).
    """
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{lat1},{lng1}:{lat2},{lng2}/json"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true"
    }

    try:
        async with httpx.AsyncClient(timeout=TOMTOM_TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return None

        route_summary = data["routes"][0]["summary"]
        return {
            "distance_km": round(route_summary["lengthInMeters"] / 1000, 2),
            "duration_min": round(route_summary["travelTimeInSeconds"] / 60, 1),
        }

    except (httpx.HTTPError, httpx.TimeoutException, KeyError, Exception) as e:
        print(f"[TomTom] API error: {e}")
        return None

def _haversine_fallback(lat1: float, lng1: float, lat2: float, lng2: float) -> dict:
    """Haversine fallback when OSRM is unreachable."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    dist_km = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return {
        "distance_km": round(dist_km, 2),
        "duration_min": round((dist_km / 40.0) * 60, 1),  # assume 40 km/h city
    }


async def get_travel_time_with_fallback(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> dict:
    """
    Get travel time via TomTom Traffic API, falling back to Haversine if unavailable.
    Always returns a valid dict with distance_km and duration_min.
    """
    result = await get_real_travel_time(lat1, lng1, lat2, lng2)
    if result is not None:
        result["source"] = "tomtom"
        return result

    fallback = _haversine_fallback(lat1, lng1, lat2, lng2)
    fallback["source"] = "haversine_fallback"
    return fallback


# ─── Open-Meteo — Live Weather ──────────────────────────────────

async def get_weather(lat: float, lng: float) -> dict:
    """
    Call Open-Meteo to get current weather at the given location.

    Returns
    -------
    dict with keys:
        rain_mm, wind_kmh, condition (good/moderate/bad),
        visit_recommendation (physique/physique_possible/en_ligne),
        description (human-readable French text)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "rain,windspeed_10m,weathercode",
        "timezone": "Africa/Tunis",
    }

    try:
        async with httpx.AsyncClient(timeout=METEO_TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        current = data["current"]
        rain = float(current.get("rain", 0))
        wind = float(current.get("windspeed_10m", 0))
        weather_code = int(current.get("weathercode", 0))

        # Decision logic
        if rain > 3 or wind > 45:
            condition = "bad"
            recommendation = "en_ligne"
            description = "Météo défavorable — fortes pluies ou vents violents"
        elif rain > 1 or wind > 25:
            condition = "moderate"
            recommendation = "physique_possible"
            description = "Météo incertaine — visites physiques possibles avec prudence"
        else:
            condition = "good"
            recommendation = "physique"
            description = "Beau temps — conditions idéales pour les visites terrain"

        return {
            "rain_mm": rain,
            "wind_kmh": wind,
            "weather_code": weather_code,
            "condition": condition,
            "visit_recommendation": recommendation,
            "description": description,
        }

    except (httpx.HTTPError, httpx.TimeoutException, KeyError, Exception) as e:
        print(f"[Open-Meteo] API error: {e}")
        # Default to "good" on failure — don't block visits because of API issues
        return {
            "rain_mm": 0,
            "wind_kmh": 0,
            "weather_code": 0,
            "condition": "unknown",
            "visit_recommendation": "physique",
            "description": "Données météo indisponibles",
        }
