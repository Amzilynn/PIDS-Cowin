"""
Route Optimizer — decides the optimal visit order for a delegate's day.

Uses a greedy nearest-neighbor heuristic.
- Sync version: Haversine distances (fallback / data generation)
- Async version: OSRM real road distances + Open-Meteo weather
Input : delegate starting position + list of doctors to visit
Output: ordered list with estimated travel times between stops
"""

import math
import asyncio
import logging
from typing import List, Dict, Tuple

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False

from dso4.models.realtime import get_travel_time_with_fallback, get_weather


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates."""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_travel_time_min(distance_km: float, avg_speed_kmh: float = 40.0) -> float:
    """Estimate travel time in minutes given distance and average city speed."""
    if distance_km <= 0:
        return 0.0
    return round((distance_km / avg_speed_kmh) * 60, 1)


def optimize_route(
    start_lat: float,
    start_lng: float,
    visits: List[Dict],
) -> List[Dict]:
    """
    Greedy nearest-neighbor route optimization.

    Parameters
    ----------
    start_lat, start_lng : float
        Delegate's starting coordinates.
    visits : list of dict
        Each dict must have at minimum: 'latitude', 'longitude', and an 'id'.

    Returns
    -------
    list of dict
        Same visits, reordered, with 'travel_distance_km' and 'travel_time_min'
        fields added to each entry.
    """
    if not visits:
        return []

    remaining = list(visits)
    ordered = []
    current_lat = start_lat
    current_lng = start_lng
    total_distance = 0.0

    while remaining:
        # Find the nearest unvisited doctor
        best_idx = 0
        best_dist = float("inf")

        for i, v in enumerate(remaining):
            d = haversine(current_lat, current_lng,
                          float(v["latitude"]), float(v["longitude"]))
            if d < best_dist:
                best_dist = d
                best_idx = i

        chosen = remaining.pop(best_idx)
        chosen["travel_distance_km"] = round(best_dist, 2)
        chosen["travel_time_min"] = estimate_travel_time_min(best_dist)
        total_distance += best_dist

        ordered.append(chosen)

        current_lat = float(chosen["latitude"])
        current_lng = float(chosen["longitude"])

    return ordered


def calculate_total_distance(visits: List[Dict]) -> float:
    """Sum up the total travel distance from an optimized route."""
    return round(sum(v.get("travel_distance_km", 0) for v in visits), 2)


def calculate_total_travel_time(visits: List[Dict]) -> float:
    """Sum up total travel time from an optimized route."""
    return round(sum(v.get("travel_time_min", 0) for v in visits), 1)


def optimize_with_ortools(start_lat: float, start_lng: float, visits: List[Dict]) -> List[Dict]:
    """Sort visits mathematically using the optimal TSP (Traveling Salesperson) solver."""
    if not visits:
        return []
        
    all_points = [(start_lat, start_lng)] + [
        (float(v["latitude"]), float(v["longitude"])) for v in visits
    ]
    
    n = len(all_points)
    distance_matrix = []
    
    for i in range(n):
        row = []
        for j in range(n):
            d = haversine(all_points[i][0], all_points[i][1],
                         all_points[j][0], all_points[j][1])
            row.append(int(d * 1000))  # convert to meters as integer
        distance_matrix.append(row)
        
    # OR-Tools setup
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
        
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Search parameters
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = 3
    
    solution = routing.SolveWithParameters(search_params)
    
    # Extract ordered route
    ordered = []
    if solution:
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node > 0:  # skip start point
                ordered.append(visits[node - 1])
            index = solution.Value(routing.NextVar(index))
        return ordered
    else:
        logging.warning("[OR-Tools] Failed to find solution. Falling back to original order.")
        return list(visits)


async def optimize_route_realtime(
    start_lat: float,
    start_lng: float,
    visits: List[Dict],
) -> Tuple[List[Dict], dict]:
    """
    Real-time route optimization using OSRM road distances + Open-Meteo weather.

    Parameters
    ----------
    start_lat, start_lng : float
        Delegate's starting coordinates.
    visits : list of dict
        Each dict must have at minimum: 'latitude', 'longitude', and an 'id'.

    Returns
    -------
    (ordered_visits, weather_info) : tuple
        ordered_visits: visits reordered with real travel data
        weather_info: current weather conditions at the delegate's location
    """
    if not visits:
        weather = await get_weather(start_lat, start_lng)
        return [], weather

    # Step 1: Fetch weather at delegate's location
    weather = await get_weather(start_lat, start_lng)

    # Step 2: Optimal TSP sort
    if HAS_ORTOOLS:
        ordered_tsp = optimize_with_ortools(start_lat, start_lng, visits)
    else:
        # Fallback to pure greedy if ortools failed to import
        ordered_tsp = optimize_route(start_lat, start_lng, visits)
        
    ordered = []
    current_lat = start_lat
    current_lng = start_lng
    total_distance = 0.0

    # Step 3: Call TomTom sequentially for the perfectly sorted path
    for chosen in ordered_tsp:
        v_lat = float(chosen["latitude"])
        v_lng = float(chosen["longitude"])

        # Launch exactly ONE TomTom request for the chosen hop
        best_travel = await get_travel_time_with_fallback(current_lat, current_lng, v_lat, v_lng)

        chosen["travel_time_min"] = best_travel["duration_min"]
        chosen["travel_distance_km"] = best_travel["distance_km"]
        chosen["travel_source"] = best_travel.get("source", "unknown")

        # Step 3: Apply Weather Constraints
        dist = best_travel.get("distance_km", 0)
        condition = weather.get("condition", "good")
        if condition == "bad":
            chosen["type_visite"] = "en_ligne"
            chosen["weather_override"] = True
            chosen["weather_reason"] = "Mauvaises conditions météo"
        elif condition == "moderate" and dist > 10:
            chosen["type_visite"] = "en_ligne"
            chosen["weather_override"] = True
            chosen["weather_reason"] = "Distance élevée + météo modérée"
        else:
            chosen["weather_override"] = False

        total_distance += best_travel["distance_km"]
        ordered.append(chosen)

        current_lat = v_lat
        current_lng = v_lng

    return ordered, weather

