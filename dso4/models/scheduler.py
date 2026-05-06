"""
Schedule Builder — generates time-blocked daily plans for a delegate.

Input : optimized route + visit durations + delegate availability
Output: time-blocked schedule with travel windows
Rules : 08:00-18:00 working hours, 12:00-13:00 lunch break
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional


# Working day configuration
WORK_START = 8 * 60       # 08:00 in minutes
WORK_END = 18 * 60        # 18:00 in minutes
LUNCH_START = 12 * 60     # 12:00
LUNCH_END = 13 * 60       # 13:00
DEFAULT_PHYSICAL_DURATION = 30   # minutes
DEFAULT_ONLINE_DURATION = 15     # minutes
BUFFER_BETWEEN_VISITS = 5        # minutes buffer between visits


def minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM format."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def build_schedule(
    optimized_visits: List[Dict],
    date_str: Optional[str] = None,
    delegate_name: str = "Delegue",
) -> Dict:
    """
    Build a time-blocked daily schedule from an optimized route.

    Parameters
    ----------
    optimized_visits : list of dict
        Visits in optimized order. Each must have:
        - travel_time_min (float): travel time to this stop
        - type_visite (str): "physique" or "en_ligne"
        - duree_min (int, optional): visit duration
        Plus doctor info (nom, prenom, specialite, etc.)

    date_str : str, optional
        Date for the schedule (YYYY-MM-DD). Defaults to today.

    delegate_name : str
        Name of the delegate for the schedule header.

    Returns
    -------
    dict with schedule details and time blocks.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    schedule_blocks = []
    current_time = WORK_START  # Start at 08:00
    total_travel = 0.0
    total_visit_time = 0
    visits_scheduled = 0

    for visit in optimized_visits:
        travel_time = int(visit.get("travel_time_min", 0))
        visit_type = visit.get("type_visite", "physique")

        # Determine visit duration
        duree = visit.get("duree_min")
        if duree is None or duree == 0:
            duree = DEFAULT_PHYSICAL_DURATION if visit_type == "physique" else DEFAULT_ONLINE_DURATION
        else:
            duree = int(duree)

        # Add travel time
        if travel_time > 0:
            travel_start = current_time
            current_time += travel_time

            # If we'd arrive during lunch, push to after lunch
            if travel_start < LUNCH_START and current_time >= LUNCH_START:
                current_time = LUNCH_END

            schedule_blocks.append({
                "type": "trajet",
                "start": minutes_to_time(travel_start),
                "end": minutes_to_time(current_time),
                "duration_min": travel_time,
                "description": f"Trajet vers {visit.get('nom', '')} {visit.get('prenom', '')}",
                "distance_km": visit.get("travel_distance_km", 0),
            })
            total_travel += travel_time

        # Check if lunch break needed
        if current_time < LUNCH_START and current_time + duree > LUNCH_START:
            # Visit would overlap lunch, schedule lunch first
            schedule_blocks.append({
                "type": "pause",
                "start": minutes_to_time(LUNCH_START),
                "end": minutes_to_time(LUNCH_END),
                "duration_min": 60,
                "description": "Pause dejeuner",
            })
            current_time = LUNCH_END
        elif LUNCH_START <= current_time < LUNCH_END:
            # We're in lunch time, add lunch break
            schedule_blocks.append({
                "type": "pause",
                "start": minutes_to_time(current_time),
                "end": minutes_to_time(LUNCH_END),
                "duration_min": LUNCH_END - current_time,
                "description": "Pause dejeuner",
            })
            current_time = LUNCH_END

        # Check if we've exceeded working hours
        if current_time + duree > WORK_END:
            # Can't fit this visit, mark as overflow
            schedule_blocks.append({
                "type": "overflow",
                "start": minutes_to_time(current_time),
                "end": minutes_to_time(current_time + duree),
                "duration_min": duree,
                "visit": _format_visit_block(visit, current_time, duree, visit_type),
                "description": f"Visite depassant les heures de travail",
            })
            break

        # Schedule the visit
        visit_start = current_time
        visit_end = current_time + duree

        block = {
            "type": "visite",
            "start": minutes_to_time(visit_start),
            "end": minutes_to_time(visit_end),
            "duration_min": duree,
            "visit_type": visit_type,
            **_format_visit_block(visit, visit_start, duree, visit_type),
        }
        schedule_blocks.append(block)

        current_time = visit_end + BUFFER_BETWEEN_VISITS
        total_visit_time += duree
        visits_scheduled += 1

    # Summary statistics
    efficiency = 0
    if total_visit_time + total_travel > 0:
        efficiency = round((total_visit_time / (total_visit_time + total_travel)) * 100, 1)

    return {
        "date": date_str,
        "delegate": delegate_name,
        "work_start": minutes_to_time(WORK_START),
        "work_end": minutes_to_time(WORK_END),
        "visits_scheduled": visits_scheduled,
        "total_visits": len(optimized_visits),
        "total_travel_min": round(total_travel, 1),
        "total_visit_time_min": total_visit_time,
        "efficiency_pct": efficiency,
        "blocks": schedule_blocks,
    }


def _format_visit_block(visit: Dict, start_min: int, duree: int, visit_type: str) -> Dict:
    """Format a visit into a schedule block with clean keys."""
    return {
        "medecin_id": visit.get("medecin_id") or visit.get("id", 0),
        "medecin_nom": f"{visit.get('nom', '')} {visit.get('prenom', '')}".strip(),
        "specialite": visit.get("specialite", visit.get("specialite_medecin", "")),
        "adresse": visit.get("adresse", ""),
        "latitude": float(visit.get("latitude", 0)),
        "longitude": float(visit.get("longitude", 0)),
        "visit_type": visit_type,
        "travel_distance_km": visit.get("travel_distance_km", 0),
        "travel_time_min": visit.get("travel_time_min"),
        "travel_source": visit.get("travel_source"),
        "weather_override": visit.get("weather_override", False),
    }

