"""
Build Complete Italian Provinces Database from OSM
Downloads all 107 Italian provinces and overwrites cities_database.json
Runtime: ~5-6 minutes (2s rate limit per city)
"""

import sys
from pathlib import Path
import json
import time
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from osm_provider import OSMProvider

# Complete list of 107 Italian provinces
ALL_ITALIAN_PROVINCES = [
    # Lombardia (12)
    "Milano", "Bergamo", "Brescia", "Como", "Cremona", "Lecco", "Lodi", 
    "Mantova", "Monza", "Pavia", "Sondrio", "Varese",
    
    # Piemonte (8)
    "Torino", "Alessandria", "Asti", "Biella", "Cuneo", "Novara", 
    "Verbania", "Vercelli",
    
    # Liguria (4)
    "Genova", "Imperia", "La Spezia", "Savona",
    
    # Valle d'Aosta (1)
    "Aosta",
    
    # Veneto (7)
    "Venezia", "Belluno", "Padova", "Rovigo", "Treviso", "Verona", "Vicenza",
    
    # Friuli-Venezia Giulia (4)
    "Trieste", "Gorizia", "Pordenone", "Udine",
    
    # Trentino-Alto Adige (2)
    "Trento", "Bolzano",
    
    # Emilia-Romagna (9)
    "Bologna", "Ferrara", "Forlì", "Modena", "Parma", "Piacenza", 
    "Ravenna", "Reggio Emilia", "Rimini",
    
    # Toscana (10)
    "Firenze", "Arezzo", "Grosseto", "Livorno", "Lucca", "Massa", 
    "Pisa", "Pistoia", "Prato", "Siena",
    
    # Umbria (2)
    "Perugia", "Terni",
    
    # Marche (5)
    "Ancona", "Ascoli Piceno", "Fermo", "Macerata", "Pesaro",
    
    # Lazio (5)
    "Roma", "Frosinone", "Latina", "Rieti", "Viterbo",
    
    # Abruzzo (4)
    "L'Aquila", "Chieti", "Pescara", "Teramo",
    
    # Molise (2)
    "Campobasso", "Isernia",
    
    # Campania (5)
    "Napoli", "Avellino", "Benevento", "Caserta", "Salerno",
    
    # Puglia (6)
    "Bari", "Barletta", "Brindisi", "Foggia", "Lecce", "Taranto",
    
    # Basilicata (2)
    "Potenza", "Matera",
    
    # Calabria (5)
    "Catanzaro", "Cosenza", "Crotone", "Reggio Calabria", "Vibo Valentia",
    
    # Sicilia (9)
    "Palermo", "Agrigento", "Caltanissetta", "Catania", "Enna", "Messina", 
    "Ragusa", "Siracusa", "Trapani",
    
    # Sardegna (4)
    "Cagliari", "Nuoro", "Oristano", "Sassari"
]

# Interest categories mapping for OSM POIs
INTEREST_CATEGORIES = {
    "arte": ["museo", "galleria", "teatro"],
    "storia": ["castello", "monumento", "sito_archeologico"],
    "natura": ["parco", "giardino", "riserva_naturale"],
    "cibo": ["ristorante", "mercato", "enogastronomia"],
    "mare": ["spiaggia", "porto", "lungomare"],
    "montagna": ["montagna", "rifugio", "ski"]
}

def categorize_poi(poi):
    """Assign categories to a POI based on its type"""
    categories = []
    osm_type = poi.get('osm_type', '').lower()
    name = poi.get('name', '').lower()
    
    # Arte
    if any(word in osm_type or word in name for word in ['museum', 'gallery', 'theatre', 'art', 'museo', 'galleria']):
        categories.append('arte')
    
    # Storia
    if any(word in osm_type or word in name for word in ['castle', 'monument', 'archaeological', 'historic', 'castello']):
        categories.append('storia')
    
    # Natura
    if any(word in osm_type or word in name for word in ['park', 'garden', 'nature', 'parco', 'giardino']):
        categories.append('natura')
    
    # Default to cultura if no specific category
    if not categories:
        categories.append('cultura')
    
    return categories

def build_complete_database():
    """Build complete database from all Italian provinces"""
    
    osm = OSMProvider()
    cities_data = []
    failed_cities = []
    
    print("="*70)
    print("🇮🇹 BUILDING COMPLETE ITALIAN PROVINCES DATABASE")
    print("="*70)
    print(f"📍 Total provinces: {len(ALL_ITALIAN_PROVINCES)}")
    print(f"⏱️  Estimated time: ~{len(ALL_ITALIAN_PROVINCES) * 2 // 60} minutes")
    print(f"🌐 Source: OpenStreetMap (Overpass + Nominatim)")
    print("="*70)
    print()
    
    start_time = time.time()
    
    for i, city_name in enumerate(ALL_ITALIAN_PROVINCES, 1):
        elapsed = time.time() - start_time
        eta = (elapsed / i) * (len(ALL_ITALIAN_PROVINCES) - i) if i > 0 else 0
        
        print(f"[{i:3d}/{len(ALL_ITALIAN_PROVINCES)}] {city_name:20s} ", end="", flush=True)
        
        # Retry mechanism for 504 errors
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                if retry_count > 0:
                    print(f"\n   🔄 Retry {retry_count}/{max_retries}... ", end="", flush=True)
                    time.sleep(5)  # Wait 5 seconds before retry
                if retry_count > 0:
                    print(f"\n   🔄 Retry {retry_count}/{max_retries}... ", end="", flush=True)
                    time.sleep(5)  # Wait 5 seconds before retry
            
                # Get coordinates
                coords = osm.get_city_coordinates(city_name)
                if not coords:
                    print("❌ No coordinates")
                    failed_cities.append({"name": city_name, "reason": "no_coordinates"})
                    break  # Exit retry loop
                
                # Validate Italy location
                display_name = coords.get('display_name', '')
                if 'Italy' not in display_name and 'Italia' not in display_name:
                    print(f"❌ Not in Italy")
                    failed_cities.append({"name": city_name, "reason": "not_italy"})
                    break  # Exit retry loop
                
                # Extract region
                parts = display_name.split(', ')
                region = "Unknown"
                italian_regions = [
                    "Lombardia", "Piemonte", "Liguria", "Valle d'Aosta", 
                    "Veneto", "Friuli-Venezia Giulia", "Trentino-Alto Adige",
                    "Emilia-Romagna", "Toscana", "Umbria", "Marche", "Lazio",
                    "Abruzzo", "Molise", "Campania", "Puglia", "Basilicata",
                    "Calabria", "Sicilia", "Sardegna"
                ]
                for part in parts:
                    if part in italian_regions:
                        region = part
                        break
                
                # Get train station
                station = osm.get_train_station(city_name)
                station_code = None
                station_name = None
                
                if station:
                    station_name = station.get('name', 'Unknown')
                    # Generate a pseudo station code (would need real API for actual codes)
                    station_code = f"S{hash(city_name) % 100000:05d}"
                
                # Get POIs
                pois = osm.get_city_pois(city_name)
                
                # Convert POIs to database format
                attractions = []
                for poi in pois[:30]:  # Keep top 30 POIs
                    categories = categorize_poi(poi)
                    
                    attraction = {
                        "name": poi.get('name', 'Unknown'),
                        "type": poi.get('osm_type', 'attrazione'),
                        "rating": poi.get('rating', 8.0),
                        "duration_hours": poi.get('duration_hours', 2.0),
                        "cost_euro": poi.get('cost', 10),
                        "popularity": poi.get('popularity', 7.0),
                        "categories": categories,
                        "lat": poi.get('lat'),
                        "lon": poi.get('lon')
                    }
                    attractions.append(attraction)
                
                # Determine city categories based on POIs
                city_categories = set()
                for poi in pois:
                    city_categories.update(categorize_poi(poi))
                city_categories = list(city_categories)[:5]  # Max 5 categories
                
                if not city_categories:
                    city_categories = ["cultura", "storia"]
                
                # Build city entry in cities_database.json format
                city_entry = {
                    "id": city_name.lower().replace(" ", "_").replace("'", ""),
                    "name": city_name,
                    "region": region,
                    "station_code": station_code,
                    "station_name": station_name,
                    "coordinates": {
                        "lat": float(coords['lat']),
                        "lon": float(coords['lon'])
                    },
                    "population": None,  # Would need additional API
                    "categories": city_categories,
                    "tags": [],
                    "description": f"Città di {city_name}, {region}",
                    "min_stay_days": 1.0,
                    "attractions": attractions
                }
                
                cities_data.append(city_entry)
                
                # Status
                status = "✅"
                if not station:
                    status = "⚠️"
                
                print(f"{status} {len(pois):3d} POIs | ETA: {int(eta//60)}m {int(eta%60)}s")
                success = True  # Mark as successful
                
            except Exception as e:
                error_msg = str(e)
                if "504" in error_msg or "Gateway Timeout" in error_msg:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"❌ Timeout after {max_retries} retries")
                        failed_cities.append({"name": city_name, "reason": "504_timeout_after_retries"})
                else:
                    print(f"❌ Error: {error_msg[:40]}")
                    failed_cities.append({"name": city_name, "reason": error_msg})
                    break  # Exit retry loop for non-504 errors
                    break  # Exit retry loop for non-504 errors
        
        # Progressive save every 10 cities
        if i % 10 == 0 and cities_data:
            checkpoint_path = Path(__file__).parent.parent / "data" / f"checkpoint_{i}.json"
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump({"cities": cities_data, "processed": i}, f, indent=2, ensure_ascii=False)
            print(f"\n   💾 Checkpoint saved: {i} cities processed")
        
        # Rate limiting
        if i < len(ALL_ITALIAN_PROVINCES):
            time.sleep(2)
    
    # Build final database structure
    database = {
        "metadata": {
            "version": "2.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "OpenStreetMap (Overpass API + Nominatim)",
            "total_cities": len(cities_data),
            "description": "Complete database of Italian provinces with POIs"
        },
        "categories_info": {
            "arte": "Musei, gallerie, teatri",
            "storia": "Monumenti, castelli, siti archeologici",
            "natura": "Parchi, giardini, riserve naturali",
            "cibo": "Ristoranti, mercati, enogastronomia",
            "mare": "Spiagge, porti, lungomare",
            "montagna": "Montagne, rifugi, sci",
            "cultura": "Centri culturali, biblioteche",
            "shopping": "Negozi, mercati",
            "business": "Centri affari, congressi"
        },
        "cities": cities_data
    }
    
    # Save to cities_database.json (OVERWRITE)
    output_path = Path(__file__).parent.parent / "data" / "cities_database.json"
    
    # Backup old database first
    if output_path.exists():
        backup_path = output_path.parent / f"cities_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(old_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Backup saved: {backup_path.name}")
    
    # Write new database
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    total_time = time.time() - start_time
    
    print("\n" + "="*70)
    print("✅ DATABASE BUILD COMPLETE")
    print("="*70)
    print(f"📁 Output: {output_path}")
    print(f"⏱️  Total time: {int(total_time//60)}m {int(total_time%60)}s")
    print(f"📊 Statistics:")
    print(f"   • Total provinces: {len(ALL_ITALIAN_PROVINCES)}")
    print(f"   • Successfully processed: {len(cities_data)}")
    print(f"   • Failed: {len(failed_cities)}")
    print(f"   • With train stations: {sum(1 for c in cities_data if c['station_code'])}")
    print(f"   • Total POIs: {sum(len(c['attractions']) for c in cities_data)}")
    
    if failed_cities:
        print(f"\n❌ Failed cities ({len(failed_cities)}):")
        for fail in failed_cities[:10]:  # Show first 10
            print(f"   • {fail['name']}: {fail['reason'][:50]}")
        if len(failed_cities) > 10:
            print(f"   ... and {len(failed_cities) - 10} more")
    
    print("="*70)
    
    return database

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will overwrite data/cities_database.json")
    print("⏱️  Estimated runtime: 5-6 minutes\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response in ['yes', 'y', 'si', 'sì']:
        build_complete_database()
    else:
        print("❌ Operation cancelled")
