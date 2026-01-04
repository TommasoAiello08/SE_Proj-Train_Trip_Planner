"""
Consolidate cached OSM data into a static database
Uses existing cache files to avoid API calls
"""

import json
from pathlib import Path

# Main provinces from map_planner.html with their coordinates
PROVINCES_COORDS = {
    'Milano': {'lat': 45.4642, 'lon': 9.1900, 'region': 'Lombardia'},
    'Roma': {'lat': 41.9028, 'lon': 12.4964, 'region': 'Lazio'},
    'Firenze': {'lat': 43.7696, 'lon': 11.2558, 'region': 'Toscana'},
    'Venezia': {'lat': 45.4408, 'lon': 12.3155, 'region': 'Veneto'},
    'Napoli': {'lat': 40.8518, 'lon': 14.2681, 'region': 'Campania'},
    'Torino': {'lat': 45.0703, 'lon': 7.6869, 'region': 'Piemonte'},
    'Bologna': {'lat': 44.4949, 'lon': 11.3426, 'region': 'Emilia-Romagna'},
    'Verona': {'lat': 45.4384, 'lon': 10.9916, 'region': 'Veneto'},
    'Genova': {'lat': 44.4056, 'lon': 8.9463, 'region': 'Liguria'},
    'Pisa': {'lat': 43.7228, 'lon': 10.4017, 'region': 'Toscana'},
    'Bergamo': {'lat': 45.6983, 'lon': 9.6773, 'region': 'Lombardia'},
    'Brescia': {'lat': 45.5416, 'lon': 10.2118, 'region': 'Lombardia'},
    'Padova': {'lat': 45.4064, 'lon': 11.8768, 'region': 'Veneto'},
    'Siena': {'lat': 43.3188, 'lon': 11.3308, 'region': 'Toscana'},
    'Perugia': {'lat': 43.1107, 'lon': 12.3908, 'region': 'Umbria'},
    'Ancona': {'lat': 43.6158, 'lon': 13.5189, 'region': 'Marche'},
    'Bari': {'lat': 41.1171, 'lon': 16.8719, 'region': 'Puglia'},
    'Palermo': {'lat': 38.1157, 'lon': 13.3615, 'region': 'Sicilia'},
    'Catania': {'lat': 37.5079, 'lon': 15.0830, 'region': 'Sicilia'},
    'Cagliari': {'lat': 39.2238, 'lon': 9.1217, 'region': 'Sardegna'}
}

def consolidate_database():
    """Build database from cached OSM data + manual coordinates"""
    
    cache_dir = Path(__file__).parent.parent / "cache" / "osm"
    cities_data = []
    
    print(f"🇮🇹 Consolidating database from cache and coordinates...")
    print(f"📁 Cache directory: {cache_dir}\n")
    
    for city_name, coords_data in PROVINCES_COORDS.items():
        city_lower = city_name.lower().replace(" ", "_")
        cache_file = cache_dir / f"{city_lower}.json"
        
        print(f"Processing {city_name}... ", end="")
        
        # Base city entry with coordinates
        city_entry = {
            "id": city_lower,
            "name": city_name,
            "region": coords_data['region'],
            "coordinates": {
                "lat": coords_data['lat'],
                "lon": coords_data['lon']
            },
            "has_train_station": None,  # Unknown without OSM data
            "station_info": None,
            "poi_count": 0,
            "pois": []
        }
        
        # If cache exists, load POIs and station info
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Update with cached data
                pois = cached_data.get('pois', [])
                city_entry['poi_count'] = len(pois)
                city_entry['pois'] = pois
                city_entry['has_train_station'] = True  # If we have POIs, likely has station
                
                # Try to extract station info from coordinates
                if 'coordinates' in cached_data:
                    city_entry['coordinates'] = cached_data['coordinates']
                
                print(f"✅ {len(pois)} POIs from cache")
            except Exception as e:
                print(f"⚠️  Cache error: {e}, using coordinates only")
        else:
            print("📍 Coordinates only (no cache)")
        
        cities_data.append(city_entry)
    
    # Save consolidated database
    output_path = Path(__file__).parent.parent / "data" / "provinces_static.json"
    
    database = {
        "metadata": {
            "version": "1.0",
            "generated": "2026-01-04",
            "total_provinces": len(PROVINCES_COORDS),
            "description": "Static database of 20 main Italian provinces",
            "source": "OSM cache + manual coordinates from map_planner.html"
        },
        "cities": cities_data
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Database saved to: {output_path}")
    print(f"📊 Statistics:")
    print(f"   - Total provinces: {len(cities_data)}")
    print(f"   - With POI data: {sum(1 for c in cities_data if c['poi_count'] > 0)}")
    print(f"   - With coordinates only: {sum(1 for c in cities_data if c['poi_count'] == 0)}")
    
    return database

if __name__ == "__main__":
    consolidate_database()
