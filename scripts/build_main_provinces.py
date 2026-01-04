"""
Script to build database of the 20 main Italian provinces used in the frontend
Faster alternative to downloading all 107 provinces
"""

import sys
from pathlib import Path
import json
import time

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from osm_provider import OSMProvider

# List of 20 main provinces used in map_planner.html
MAIN_PROVINCES = [
    "Milano", "Roma", "Firenze", "Venezia", "Napoli",
    "Torino", "Bologna", "Verona", "Genova", "Pisa",
    "Bergamo", "Brescia", "Padova", "Siena", "Perugia",
    "Ancona", "Bari", "Palermo", "Catania", "Cagliari"
]

def build_database():
    """Build database of 20 main Italian provinces"""
    
    osm = OSMProvider()
    cities_data = []
    failed_cities = []
    
    print(f"🇮🇹 Building database for {len(MAIN_PROVINCES)} main Italian provinces...")
    print(f"⏱️  This will take ~{len(MAIN_PROVINCES) * 2} seconds (2s rate limit per city)\n")
    
    for i, city_name in enumerate(MAIN_PROVINCES, 1):
        print(f"[{i}/{len(MAIN_PROVINCES)}] Processing {city_name}...", end=" ")
        
        try:
            # Get coordinates
            coords = osm.get_city_coordinates(city_name)
            if not coords:
                print("❌ No coordinates found")
                failed_cities.append({"name": city_name, "reason": "no_coordinates"})
                continue
            
            # Check if in Italy
            display_name = coords.get('display_name', '')
            if 'Italy' not in display_name and 'Italia' not in display_name:
                print(f"❌ Not in Italy: {display_name}")
                failed_cities.append({"name": city_name, "reason": "not_italy"})
                continue
            
            # Get train station
            station = osm.get_train_station(city_name)
            if not station:
                print("⚠️  No train station")
            
            # Get POIs
            pois = osm.get_city_pois(city_name)
            
            # Extract region from display_name
            parts = display_name.split(', ')
            region = "Unknown"
            for part in parts:
                if part in ["Lombardia", "Piemonte", "Liguria", "Valle d'Aosta", 
                           "Veneto", "Friuli-Venezia Giulia", "Trentino-Alto Adige",
                           "Emilia-Romagna", "Toscana", "Umbria", "Marche", "Lazio",
                           "Abruzzo", "Molise", "Campania", "Puglia", "Basilicata",
                           "Calabria", "Sicilia", "Sardegna"]:
                    region = part
                    break
            
            # Build city entry
            city_entry = {
                "id": city_name.lower().replace(" ", "_").replace("'", ""),
                "name": city_name,
                "region": region,
                "coordinates": {
                    "lat": float(coords['lat']),
                    "lon": float(coords['lon'])
                },
                "display_name": display_name,
                "has_train_station": station is not None,
                "station_info": {
                    "name": station.get('name', 'Unknown') if station else None,
                    "lat": station.get('lat') if station else None,
                    "lon": station.get('lon') if station else None
                } if station else None,
                "poi_count": len(pois),
                "pois": pois  # Keep all POIs since it's only 20 cities
            }
            
            cities_data.append(city_entry)
            
            status = "✅"
            if not station:
                status = "⚠️ (no station)"
            print(f"{status} {len(pois)} POIs")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            failed_cities.append({"name": city_name, "reason": str(e)})
        
        # Rate limiting (2 seconds between requests)
        if i < len(MAIN_PROVINCES):
            time.sleep(2)
    
    # Save to JSON
    output_path = Path(__file__).parent.parent / "data" / "provinces_main.json"
    
    database = {
        "metadata": {
            "version": "1.0",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_provinces": len(MAIN_PROVINCES),
            "successful": len(cities_data),
            "failed": len(failed_cities),
            "description": "Database of 20 main Italian provinces used in frontend"
        },
        "cities": cities_data,
        "failed": failed_cities
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Database saved to: {output_path}")
    print(f"📊 Statistics:")
    print(f"   - Total provinces: {len(MAIN_PROVINCES)}")
    print(f"   - Successful: {len(cities_data)}")
    print(f"   - Failed: {len(failed_cities)}")
    print(f"   - With train station: {sum(1 for c in cities_data if c['has_train_station'])}")
    
    if failed_cities:
        print(f"\n❌ Failed cities:")
        for fail in failed_cities:
            print(f"   - {fail['name']}: {fail['reason']}")
    
    return database

if __name__ == "__main__":
    build_database()
