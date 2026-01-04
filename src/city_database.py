"""
City Database Manager
Manages Italian cities database for the trip planner with OSM on-demand support
"""

import json
from typing import List, Dict, Optional
from pathlib import Path

# Conditional import for OSM provider
try:
    from osm_provider import OSMProvider
except ImportError:
    from src.osm_provider import OSMProvider

class CityDatabase:
    """Manager for cities database with OSM on-demand support"""
    
    def __init__(self, db_path: str = None, use_osm: bool = True):
        if db_path is None:
            # Default: look for data/ relative to file location
            db_path = Path(__file__).parent.parent / "data" / "cities_database.json"
        self.db_path = Path(db_path)
        
        # Also load provinces static database
        self.provinces_path = Path(__file__).parent.parent / "data" / "provinces_static.json"
        
        self.cities = {}
        self.categories = {}
        self.use_osm = use_osm
        self.osm_provider = OSMProvider() if use_osm else None
        self.load_database()
    
    def load_database(self):
        """Load database from JSON file"""
        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Index by ID
        for city in data['cities']:
            self.cities[city['id']] = city
        
        # Also load provinces static database if exists
        if self.provinces_path.exists():
            with open(self.provinces_path, 'r', encoding='utf-8') as f:
                provinces_data = json.load(f)
                for city in provinces_data['cities']:
                    # Don't overwrite existing cities
                    if city['id'] not in self.cities:
                        self.cities[city['id']] = city
        
        self.categories = data.get('categories_info', {})
        self.metadata = data.get('metadata', {})
        
        print(f"✅ Database loaded: {len(self.cities)} cities")
    
    def get_city(self, city_id: str) -> Optional[Dict]:
        """Get city by ID"""
        return self.cities.get(city_id)
    
    def get_city_by_name(self, name: str) -> Optional[Dict]:
        """Get city by name (first from static DB, then from OSM)"""
        name_lower = name.lower()
        for city in self.cities.values():
            if city['name'].lower() == name_lower:
                return city
        
        # If not found and OSM enabled, query OSM on-demand
        if self.use_osm and self.osm_provider:
            print(f"🌐 City '{name}' not in static DB, querying OSM...")
            return self._fetch_city_from_osm(name)
        
        return None
    
    def is_italy(self, coords: dict) -> bool:
        # Nominatim style: display_name usually contains ", Italy"
        dn = (coords or {}).get("display_name", "") or ""
        print(dn)
        # be permissive: Italy / Italia
        return ("Italy" in dn) or ("Italia" in dn)

    def validate_osm_result(self, city_name: str, coords: dict, station: dict) -> None:
        # Must have coordinates
        if not coords or "lat" not in coords or "lon" not in coords:
            raise ValueError(f"Unsupported city '{city_name}': no coordinates found")

        # Must be in Italy
        if not self.is_italy(coords):
            raise ValueError(f"Unsupported city '{city_name}': only Italian cities are supported")

        # Must have a train station
        # (your get_train_station returns something truthy when found)
        if station:
            print(f"   🚉 Found train station: {station.get('name', 'unknown')}")
        else:
            raise ValueError(f"Unsupported city '{city_name}': no train station found")

    
    def _fetch_city_from_osm(self, city_name: str) -> Optional[Dict]:
        """Create city entry from OSM data on-demand"""
        try:
            # City coordinates
            coords = self.osm_provider.get_city_coordinates(city_name)
            if not coords:
                return None

            # Train station (require it)
            station = self.osm_provider.get_train_station(city_name)

            # Validate against your constraints (Italy + station + coords)
            self.validate_osm_result(city_name, coords, station)

            # POIs (optional, can be empty)
            pois = self.osm_provider.get_city_pois(city_name) or []

            # Build database-compatible entry
            city_entry = {
                'id': f"osm_{city_name.lower().replace(' ', '_')}",
                'name': city_name,
                'region': coords.get('display_name', '').split(',')[-2].strip()
                        if ',' in coords.get('display_name', '') else 'Unknown',

                # ✅ IMPORTANT: provide the schema expected by travel_graph
                'coordinates': {
                    'lat': float(coords['lat']),
                    'lon': float(coords['lon']),
                },

                # (optional) keep these if other code uses them
                'latitude': float(coords['lat']),
                'longitude': float(coords['lon']),

                'station_code': station.get('name', city_name),
                'attractions': pois,
                'categories': list({cat for poi in pois for cat in poi.get('categories', [])}),
                'average_cost_per_day': 60,
                'food_specialties': [],
                'osm_source': True
            }

            print(f"✅ Created city from OSM: {len(pois)} POIs found")
            return city_entry

        except ValueError as e:
            # Validation failure => treat as "unsupported city"
            print(f"❌ {e}")
            return None

        except Exception as e:
            print(f"❌ Error fetching OSM data for {city_name}: {e}")
            return None

        
    
    def get_all_cities(self) -> List[Dict]:
        """Get all cities"""
        return list(self.cities.values())
    
    def search_by_category(self, category: str) -> List[Dict]:
        """Find cities by interest category"""
        results = []
        category_lower = category.lower()
        
        for city in self.cities.values():
            if category_lower in [c.lower() for c in city['categories']]:
                results.append(city)
        
        return results
    
    def search_by_region(self, region: str) -> List[Dict]:
        """Trova città per regione"""
        results = []
        region_lower = region.lower()
        
        for city in self.cities.values():
            if city['region'].lower() == region_lower:
                results.append(city)
        
        return results
    
    def get_cities_in_radius(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """Trova città entro un raggio geografico"""
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1, lon1, lat2, lon2):
            """Calcola distanza in km tra due coordinate"""
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            km = 6371 * c
            return km
        
        results = []
        for city in self.cities.values():
            city_lat = city['coordinates']['lat']
            city_lon = city['coordinates']['lon']
            distance = haversine(lat, lon, city_lat, city_lon)
            
            if distance <= radius_km:
                results.append({
                    'city': city,
                    'distance_km': round(distance, 1)
                })
        
        # Ordina per distanza
        results.sort(key=lambda x: x['distance_km'])
        return results
    
    def calculate_city_score(self, city: Dict, user_interests: List[str], 
                            travel_time_hours: float = 0) -> float:
        """
        Calcola score di una città basato su interessi utente e tempo viaggio
        
        Args:
            city: Dati città
            user_interests: Lista categorie interessanti per l'utente
            travel_time_hours: Tempo viaggio in ore
        
        Returns:
            Score 0-1
        """
        score = 0.0
        
        # 1. Match con interessi (40%)
        if user_interests:
            city_categories = [c.lower() for c in city['categories']]
            user_interests_lower = [i.lower() for i in user_interests]
            
            matches = sum(1 for interest in user_interests_lower 
                         if interest in city_categories)
            interest_score = matches / len(user_interests_lower)
            score += interest_score * 0.4
        else:
            score += 0.4  # Nessuna preferenza = considera tutto
        
        # 2. Attrazioni (30%)
        attractions = city.get('attractions', [])
        if attractions:
            avg_rating = sum(a.get('rating', 8.0) for a in attractions) / len(attractions)
            attraction_score = avg_rating / 10.0  # Normalizza a 0-1
            score += attraction_score * 0.3
        
        # 3. Popolarità (20%)
        population = city.get('population') or 0
        if population > 0:
            popularity_score = min(population / 3000000, 1.0)  # Normalizza
            score += popularity_score * 0.2
        else:
            # Se non abbiamo population, usiamo numero di attrazioni come proxy
            if attractions:
                popularity_score = min(len(attractions) / 30, 1.0)
                score += popularity_score * 0.2
            else:
                score += 0.1  # Score minimo
        
        # 4. Penalità distanza (10%)
        # Meno tempo viaggio = migliore
        if travel_time_hours > 0:
            distance_score = max(0, 1 - (travel_time_hours / 6))  # 6h = score 0
            score += distance_score * 0.1
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_top_attractions(self, city_id: str, limit: int = 5) -> List[Dict]:
        """Ottieni top attrazioni per una città"""
        city = self.get_city(city_id)
        if not city:
            return []
        
        attractions = city.get('attractions', [])
        # Ordina per rating * popularity
        attractions_scored = [
            {**a, 'score': a['rating'] * a.get('popularity', 5) / 10}
            for a in attractions
        ]
        attractions_scored.sort(key=lambda x: x['score'], reverse=True)
        
        return attractions_scored[:limit]
    
    def estimate_daily_cost(self, city_id: str, include_attractions: bool = True) -> float:
        """Stima costo giornaliero in una città"""
        city = self.get_city(city_id)
        if not city:
            return 100.0  # Default
        
        cost = city.get('avg_hotel_price', 80)  # Hotel
        cost += 40  # Cibo medio
        
        if include_attractions:
            attractions = city.get('attractions', [])
            if attractions:
                # Media top 3 attrazioni
                top_costs = sorted([a['cost_euro'] for a in attractions], reverse=True)[:3]
                cost += sum(top_costs) / max(len(top_costs), 1)
        
        return round(cost, 2)
    
    def get_statistics(self) -> Dict:
        """Statistiche del database"""
        all_cities = self.get_all_cities()
        
        total_attractions = sum(len(c.get('attractions', [])) for c in all_cities)
        avg_attractions = total_attractions / len(all_cities) if all_cities else 0
        
        all_categories = set()
        for city in all_cities:
            all_categories.update(city.get('categories', []))
        
        return {
            'total_cities': len(all_cities),
            'total_attractions': total_attractions,
            'avg_attractions_per_city': round(avg_attractions, 1),
            'unique_categories': len(all_categories),
            'regions_covered': len(set(c['region'] for c in all_cities))
        }


# ============================================================================
# FUNZIONI DI UTILITÀ
# ============================================================================

def print_city_info(city: Dict):
    """Stampa info formattate di una città"""
    print(f"\n{'='*60}")
    print(f"🏙️  {city['name']} ({city['region']})")
    print(f"{'='*60}")
    print(f"📍 Stazione: {city['station_name']}")
    print(f"👥 Popolazione: {city['population']:,}")
    print(f"⏱️  Soggiorno minimo: {city['min_stay_days']} giorni")
    print(f"💰 Costo medio/giorno: ~€{city.get('avg_hotel_price', 80) + 50}")
    print(f"\n📝 {city['description']}")
    
    print(f"\n🎯 Categorie: {', '.join(city['categories'])}")
    print(f"🏷️  Tag: {', '.join(city['tags'])}")
    
    print(f"\n⭐ TOP ATTRAZIONI:")
    for i, attr in enumerate(city['attractions'][:5], 1):
        print(f"  {i}. {attr['name']} - ⭐{attr['rating']}/10")
        print(f"     ⏱️ {attr['duration_hours']}h | 💰 €{attr['cost_euro']}")
    
    print(f"\n🍝 Specialità: {', '.join(city['food_specialties'])}")


def demo_database_usage():
    """Demo di utilizzo del database"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          City Database Demo                             ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Carica database
    db = CityDatabase()
    
    # Statistiche
    print("\n📊 STATISTICHE DATABASE")
    print("─" * 60)
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test 1: Cerca per categoria
    print("\n\n1️⃣  CERCA CITTÀ PER CATEGORIA: 'arte'")
    print("─" * 60)
    art_cities = db.search_by_category('arte')
    print(f"Trovate {len(art_cities)} città:")
    for city in art_cities[:3]:
        print(f"  • {city['name']} - {', '.join(city['categories'][:3])}")
    
    # Test 2: Città vicine
    print("\n\n2️⃣  CITTÀ ENTRO 200 KM DA FIRENZE")
    print("─" * 60)
    florence = db.get_city('firenze')
    nearby = db.get_cities_in_radius(
        florence['coordinates']['lat'],
        florence['coordinates']['lon'],
        radius_km=200
    )
    for entry in nearby[:5]:
        print(f"  • {entry['city']['name']}: {entry['distance_km']} km")
    
    # Test 3: Calcola score
    print("\n\n3️⃣  SCORE CITTÀ PER INTERESSI ['arte', 'storia']")
    print("─" * 60)
    interests = ['arte', 'storia']
    scored_cities = []
    for city in db.get_all_cities():
        score = db.calculate_city_score(city, interests, travel_time_hours=2)
        scored_cities.append((city['name'], score))
    
    scored_cities.sort(key=lambda x: x[1], reverse=True)
    for name, score in scored_cities[:5]:
        print(f"  • {name}: {score:.2f}/1.00")
    
    # Test 4: Info dettagliate
    print("\n\n4️⃣  INFO DETTAGLIATE: ROMA")
    print_city_info(db.get_city('roma'))
    
    # Test 5: Costi
    print("\n\n5️⃣  STIMA COSTI GIORNALIERI")
    print("─" * 60)
    for city in db.get_all_cities()[:5]:
        cost = db.estimate_daily_cost(city['id'])
        print(f"  • {city['name']}: €{cost}/giorno")
    
    print("\n" + "="*60)
    print("✅ Demo completata!")


if __name__ == "__main__":
    demo_database_usage()
