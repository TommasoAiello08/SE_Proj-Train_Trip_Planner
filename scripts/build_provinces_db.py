"""
Script to build a comprehensive Italian provinces database
Downloads data from OSM for all 108 Italian provinces
"""

import sys
from pathlib import Path
import json
import time

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from osm_provider import OSMProvider

# List of all 108 Italian provinces (107 provinces + 1 metropolitan city)
ITALIAN_PROVINCES = [
    # Lombardia
    "Milano", "Bergamo", "Brescia", "Como", "Cremona", "Lecco", "Lodi", 
    "Mantova", "Monza", "Pavia", "Sondrio", "Varese",
    
    # Piemonte
    "Torino", "Alessandria", "Asti", "Biella", "Cuneo", "Novara", 
    "Verbania", "Vercelli",
    
    # Liguria
    "Genova", "Imperia", "La Spezia", "Savona",
    
    # Valle d'Aosta
    "Aosta",
    
    # Veneto
    "Venezia", "Belluno", "Padova", "Rovigo", "Treviso", "Verona", "Vicenza",
    
    # Friuli-Venezia Giulia
    "Trieste", "Gorizia", "Pordenone", "Udine",
    
    # Trentino-Alto Adige
    "Trento", "Bolzano",
    
    # Emilia-Romagna
    "Bologna", "Ferrara", "Forlì", "Modena", "Parma", "Piacenza", 
    "Ravenna", "Reggio Emilia", "Rimini",
    
    # Toscana
    "Firenze", "Arezzo", "Grosseto", "Livorno", "Lucca", "Massa", 
    "Pisa", "Pistoia", "Prato", "Siena",
    
    # Umbria
    "Perugia", "Terni",
    
    # Marche
    "Ancona", "Ascoli Piceno", "Fermo", "Macerata", "Pesaro",
    
    # Lazio
    "Roma", "Frosinone", "Latina", "Rieti", "Viterbo",
    
    # Abruzzo
    "L'Aquila", "Chieti", "Pescara", "Teramo",
    
    # Molise
    "Campobasso", "Isernia",
    
    # Campania
    "Napoli", "Avellino", "Benevento", "Caserta", "Salerno",
    
    # Puglia
    "Bari", "Barletta", "Brindisi", "Foggia", "Lecce", "Taranto",
    
    # Basilicata
    "Potenza", "Matera",
    
    # Calabria
    "Catanzaro", "Cosenza", "Crotone", "Reggio Calabria", "Vibo Valentia",
    
    # Sicilia
    "Palermo", "Agrigento", "Caltanissetta", "Catania", "Enna", "Messina", 
    "Ragusa", "Siracusa", "Trapani",
    
    # Sardegna
    "Cagliari", "Nuoro", "Oristano", "Sassari", "Sud Sardegna"
]

def build_database():
    """Build comprehensive database of Italian provinces"""
    
    osm = OSMProvider()
    cities_data = []
    failed_cities = []
    
    print(f"🇮🇹 Building database for {len(ITALIAN_PROVINCES)} Italian provinces...")
    print(f"⏱️  This will take ~{len(ITALIAN_PROVINCES) * 2} seconds (2s rate limit per city)\n")
    
    for i, city_name in enumerate(ITALIAN_PROVINCES, 1):
        print(f"[{i}/{len(ITALIAN_PROVINCES)}] Processing {city_name}...", end=" ")
        
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
                # We'll include it anyway but mark it
            
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
                "pois": pois[:20]  # Keep top 20 POIs to reduce file size
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
        if i < len(ITALIAN_PROVINCES):
            time.sleep(2)
    
    # Save to JSON
    output_path = Path(__file__).parent.parent / "data" / "provinces_full.json"
    
    database = {
        "metadata": {
            "version": "1.0",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_provinces": len(ITALIAN_PROVINCES),
            "successful": len(cities_data),
            "failed": len(failed_cities),
            "description": "Complete database of Italian provinces with OSM data"
        },
        "cities": cities_data,
        "failed": failed_cities
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Database saved to: {output_path}")
    print(f"📊 Statistics:")
    print(f"   - Total provinces: {len(ITALIAN_PROVINCES)}")
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
