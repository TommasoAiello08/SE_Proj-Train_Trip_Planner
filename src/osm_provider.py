"""
OSM Provider - Integrazione dinamica con OpenStreetMap
=======================================================

Fornisce dati POI on-demand per qualsiasi città italiana.
Include caching per evitare chiamate ripetute.
"""

import requests
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta


class OSMProvider:
    """
    Provider per dati OpenStreetMap con caching intelligente
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 secondi tra richieste
        
        # Cache
        self.cache_dir = cache_dir or (Path(__file__).parent.parent / "cache" / "osm")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(days=7)  # Cache valida 7 giorni
    
    def _rate_limit(self):
        """Applica rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, city_name: str) -> Path:
        """Ottiene path del file cache per una città"""
        safe_name = city_name.replace(" ", "_").lower()
        return self.cache_dir / f"{safe_name}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Verifica se cache è ancora valida"""
        if not cache_path.exists():
            return False
        
        # Controlla età del file
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < self.cache_ttl
    
    def _load_from_cache(self, city_name: str) -> Optional[Dict]:
        """Carica dati da cache se disponibile"""
        cache_path = self._get_cache_path(city_name)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def _save_to_cache(self, city_name: str, data: Dict):
        """Salva dati in cache"""
        cache_path = self._get_cache_path(city_name)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Errore salvataggio cache: {e}")
    
    def get_city_coordinates(self, city_name: str) -> Optional[Dict]:
        """
        Ottiene coordinate di una città italiana
        
        Returns:
            {'lat': float, 'lon': float, 'display_name': str} o None
        """
        self._rate_limit()
        
        params = {
            "q": f"{city_name}, Italia",
            "format": "json",
            "limit": 1,
            "countrycodes": "it"
        }
        
        try:
            response = requests.get(
                self.nominatim_url,
                params=params,
                headers={"User-Agent": "TrainTripPlanner/1.0"},
                timeout=10
            )
            response.raise_for_status()
            results = response.json()
            
            if results:
                return {
                    "lat": float(results[0]["lat"]),
                    "lon": float(results[0]["lon"]),
                    "display_name": results[0]["display_name"],
                    "osm_id": results[0].get("osm_id"),
                    "osm_type": results[0].get("osm_type")
                }
        except Exception as e:
            print(f"⚠️  Errore coordinate {city_name}: {e}")
        
        return None
    
    def get_city_pois(self, city_name: str, radius: int = 15000) -> List[Dict]:
        """
        Ottiene POI per una città con caching
        
        Args:
            city_name: Nome città
            radius: Raggio ricerca in metri (default 15km)
            
        Returns:
            Lista POI con name, type, rating, duration, cost, categories, lat, lon
        """
        # Controlla cache
        cached_data = self._load_from_cache(city_name)
        if cached_data:
            print(f"  💾 Cache hit per {city_name}")
            return cached_data.get('pois', [])
        
        print(f"  🌐 Interrogo OSM per {city_name}...")
        
        # Ottieni coordinate centro città
        coords = self.get_city_coordinates(city_name)
        if not coords:
            print(f"  ❌ Coordinate non trovate per {city_name}")
            return []
        
        lat, lon = coords['lat'], coords['lon']
        
        # Estrai POI (con retry per rate limiting)
        pois = self._fetch_pois_with_retry(lat, lon, radius)
        
        # Converte POI OSM in formato nostro database
        formatted_pois = self._format_pois(pois)
        
        # Salva in cache
        cache_data = {
            'city': city_name,
            'coordinates': coords,
            'pois': formatted_pois,
            'fetched_at': datetime.now().isoformat(),
            'radius': radius
        }
        self._save_to_cache(city_name, cache_data)
        
        return formatted_pois
    
    def _fetch_pois_with_retry(self, lat: float, lon: float, radius: int, max_retries: int = 3) -> List[Dict]:
        """
        Estrae POI da OSM con gestione errori e retry
        """
        # Query più semplice per evitare timeout
        query = f"""
        [out:json][timeout:45];
        (
          node["tourism"~"museum|attraction|gallery|monument|viewpoint"](around:{radius},{lat},{lon});
          node["historic"~"monument|castle|ruins|archaeological_site"](around:{radius},{lat},{lon});
          node["leisure"~"park|garden|nature_reserve"](around:{radius},{lat},{lon});
        );
        out body;
        """
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                response = requests.post(
                    self.overpass_url,
                    data={"data": query},
                    timeout=60
                )
                
                if response.status_code == 429:
                    # Too many requests - attendi più a lungo
                    wait_time = (attempt + 1) * 5
                    print(f"    ⏳ Rate limit, attendo {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                return data.get("elements", [])
                
            except requests.exceptions.Timeout:
                print(f"    ⏱️  Timeout (tentativo {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
            except Exception as e:
                print(f"    ⚠️  Errore: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        return []
    
    def _format_pois(self, osm_pois: List[Dict]) -> List[Dict]:
        """
        Converte POI OSM nel formato del nostro database
        """
        formatted = []
        
        for poi in osm_pois:
            tags = poi.get("tags", {})
            name = tags.get("name")
            
            if not name or name == "Unnamed":
                continue
            
            # Determina tipo principale
            poi_type = None
            categories = []
            
            if "tourism" in tags:
                poi_type = tags["tourism"]
                categories.append(self._map_osm_category(tags["tourism"]))
            elif "historic" in tags:
                poi_type = tags["historic"]
                categories.append("storia")
            elif "leisure" in tags:
                poi_type = tags["leisure"]
                categories.append(self._map_osm_category(tags["leisure"]))
            
            # Estrai rating da wikidata se disponibile (altrimenti stima)
            rating = self._estimate_rating(tags)
            
            formatted_poi = {
                "name": name,
                "rating": rating,
                "duration_hours": self._estimate_duration(poi_type),
                "cost": self._estimate_cost(poi_type),
                "categories": categories,
                "lat": poi.get("lat"),
                "lon": poi.get("lon"),
                "popularity": rating,  # Uso rating come proxy
                "osm_id": poi.get("id"),
                "osm_type": poi_type
            }
            
            formatted.append(formatted_poi)
        
        return formatted
    
    def _map_osm_category(self, osm_tag: str) -> str:
        """Mappa tag OSM alle nostre categorie"""
        mapping = {
            "museum": "arte",
            "gallery": "arte",
            "attraction": "cultura",
            "monument": "storia",
            "castle": "storia",
            "ruins": "storia",
            "archaeological_site": "archeologia",
            "park": "natura",
            "garden": "natura",
            "nature_reserve": "natura",
            "viewpoint": "panorama"
        }
        return mapping.get(osm_tag, "cultura")
    
    def _estimate_rating(self, tags: Dict) -> float:
        """Stima rating basato su dati disponibili"""
        # Se ha wikipedia/wikidata, probabilmente importante
        if tags.get("wikipedia") or tags.get("wikidata"):
            return 8.0
        
        # Se è heritage UNESCO
        if tags.get("heritage"):
            return 9.0
        
        # Default medio
        return 7.0
    
    def _estimate_duration(self, poi_type: str) -> float:
        """Stima durata visita basata su tipo"""
        durations = {
            "museum": 2.5,
            "gallery": 2.0,
            "castle": 2.0,
            "monument": 1.0,
            "park": 1.5,
            "attraction": 2.0
        }
        return durations.get(poi_type, 1.5)
    
    def _estimate_cost(self, poi_type: str) -> float:
        """Stima costo basato su tipo"""
        costs = {
            "museum": 12.0,
            "gallery": 10.0,
            "castle": 15.0,
            "monument": 5.0,
            "park": 0.0,
            "attraction": 10.0
        }
        return costs.get(poi_type, 8.0)
    
    def get_train_station(self, city_name: str) -> Optional[Dict]:
        """
        Trova stazione ferroviaria principale della città
        """
        self._rate_limit()
        
        # Cerca varianti nome stazione
        queries = [
            f"{city_name} Centrale",
            f"{city_name} Termini",
            f"Stazione {city_name}",
            city_name
        ]
        
        for query in queries:
            params = {
                "q": query,
                "format": "json",
                "limit": 5,
                "countrycodes": "it"
            }
            
            try:
                response = requests.get(
                    self.nominatim_url,
                    params=params,
                    headers={"User-Agent": "TrainTripPlanner/1.0"},
                    timeout=10
                )
                response.raise_for_status()
                results = response.json()
                
                # Filtra per tipo railway/stazione
                for result in results:
                    display = result["display_name"].lower()
                    result_type = result.get("type", "").lower()
                    
                    if "stazione" in display or "station" in display or result_type == "station":
                        return {
                            "name": result["display_name"],
                            "lat": float(result["lat"]),
                            "lon": float(result["lon"]),
                            "osm_id": result.get("osm_id")
                        }
            except Exception:
                continue
            
            time.sleep(0.5)  # Breve pausa tra query
        
        return None


# Test
if __name__ == "__main__":
    provider = OSMProvider()
    
    print("🧪 Test OSM Provider\n")
    
    # Test su città non nel database statico
    test_cities = ["Perugia", "Padova", "Siena"]
    
    for city in test_cities:
        print(f"\n{'='*60}")
        print(f"🏛️  {city.upper()}")
        print('='*60)
        
        # Coordinate
        coords = provider.get_city_coordinates(city)
        if coords:
            print(f"📍 {coords['lat']:.4f}, {coords['lon']:.4f}")
        
        # POI
        pois = provider.get_city_pois(city, radius=10000)
        print(f"\n🎯 POI trovati: {len(pois)}")
        
        if pois:
            for poi in pois[:5]:
                print(f"  • {poi['name']} (rating: {poi['rating']}, {poi['duration_hours']}h, €{poi['cost']})")
        
        # Stazione
        station = provider.get_train_station(city)
        if station:
            print(f"\n🚂 Stazione: {station['name']}")
