"""
Generate synthetic visites.csv from real medecins.csv and delegues.csv.
Run from the project root:
    python -m dso4.generate_data
"""

import os
import csv
import random
import math
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

MEDECINS_PATH = os.path.join(PROJECT_ROOT, "dso2", "data", "raw", "medecins.csv")
DELEGUES_PATH = os.path.join(BASE_DIR, "data", "delegues.csv")
VISITES_PATH = os.path.join(BASE_DIR, "data", "visites.csv")


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two GPS points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_csv(path, encoding="utf-8-sig"):
    """Load a CSV file, trying utf-8-sig (handles BOM) then latin-1."""
    try:
        with open(path, "r", encoding=encoding) as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return list(csv.DictReader(f))


def main():
    # Load delegates
    delegues = load_csv(DELEGUES_PATH)
    print(f"Loaded {len(delegues)} delegates")

    # Load doctors (only those with valid coordinates)
    raw_medecins = load_csv(MEDECINS_PATH)
    medecins = []
    for m in raw_medecins:
        try:
            lat = float(m["latitude"])
            lng = float(m["longitude"])
            if 30 < lat < 38 and 7 < lng < 12:  # Tunisia bounding box
                medecins.append(m)
        except (ValueError, KeyError):
            continue
    print(f"Loaded {len(medecins)} valid doctors (with Tunisian coords)")

    # For each delegate, find nearby doctors (within 30 km)
    random.seed(42)
    visites = []
    visit_id = 1
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2025, 3, 31)
    
    statuts = ["effectuée", "effectuée", "effectuée", "effectuée", "effectuée",
               "effectuée", "effectuée", "annulée", "annulée", "reportée"]
    heures = ["08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
              "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"]
    
    for d in delegues:
        d_lat = float(d["latitude"])
        d_lng = float(d["longitude"])
        
        # Find doctors within 30km of this delegate
        nearby = []
        for m in medecins:
            m_lat = float(m["latitude"])
            m_lng = float(m["longitude"])
            dist = haversine(d_lat, d_lng, m_lat, m_lng)
            if dist <= 30:
                nearby.append((m, dist))
        
        if not nearby:
            continue
        
        # Generate 40-60 visits per delegate
        num_visits = random.randint(40, 60)
        for _ in range(num_visits):
            doctor, distance = random.choice(nearby)
            
            # Random date
            days_range = (end_date - start_date).days
            visit_date = start_date + timedelta(days=random.randint(0, days_range))
            
            # Skip weekends
            while visit_date.weekday() >= 5:
                visit_date += timedelta(days=1)
            
            heure = random.choice(heures)
            statut = random.choice(statuts)
            
            # Physical vs online: further doctors more likely online
            if distance > 15:
                type_visite = random.choices(["physique", "en_ligne"], weights=[30, 70])[0]
            elif distance > 8:
                type_visite = random.choices(["physique", "en_ligne"], weights=[60, 40])[0]
            else:
                type_visite = random.choices(["physique", "en_ligne"], weights=[85, 15])[0]
            
            # Duration based on type
            if type_visite == "physique":
                duree = random.choice([20, 25, 30, 30, 30, 35, 40, 45])
            else:
                duree = random.choice([10, 15, 15, 15, 20, 20, 25])
            
            # Score: physical visits tend to score higher
            base_score = 7.0 if type_visite == "physique" else 6.0
            score = round(base_score + random.uniform(-2.5, 3.0), 1)
            score = max(1.0, min(10.0, score))
            
            # Cancelled visits get no score
            if statut == "annulée":
                score = 0.0
                duree = 0
            
            specialite = doctor.get("specialite", "Médecine générale")
            
            visites.append({
                "id": visit_id,
                "delegue_id": int(d["id"]),
                "medecin_id": int(doctor["id"]),
                "date": visit_date.strftime("%Y-%m-%d"),
                "heure": heure,
                "duree_min": duree,
                "statut": statut,
                "type_visite": type_visite,
                "score_visite": score,
                "distance_km": round(distance, 2),
                "specialite_medecin": specialite
            })
            visit_id += 1
    
    # Sort by date  
    visites.sort(key=lambda v: (v["date"], v["delegue_id"], v["heure"]))
    
    # Write visites.csv
    fieldnames = ["id", "delegue_id", "medecin_id", "date", "heure", "duree_min",
                  "statut", "type_visite", "score_visite", "distance_km", "specialite_medecin"]
    
    with open(VISITES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, v in enumerate(visites, 1):
            v["id"] = i  # Re-number after sort
            writer.writerow(v)
    
    print(f"Generated {len(visites)} visit records -> {VISITES_PATH}")


if __name__ == "__main__":
    main()
