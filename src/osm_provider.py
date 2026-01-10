"""OSM Provider: dynamic integration with OpenStreetMap.

Provides POI data on demand for any Italian city.
Includes caching to avoid repeated requests.
"""

import requests
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta


class OSMProvider:
    """
    OpenStreetMap data provider with smart caching.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests
        
        # Cache
        self.cache_dir = cache_dir or (Path(__file__).parent.parent / "cache" / "osm")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(days=7)  # Cache valid for 7 days
    
    def _rate_limit(self):
        """Apply rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, city_name: str) -> Path:
        """Return the cache file path for a city."""
        safe_name = city_name.replace(" ", "_").lower()
        return self.cache_dir / f"{safe_name}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check whether the cache entry is still valid."""
        if not cache_path.exists():
            return False
        
        # Check file age
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < self.cache_ttl
    
    def _load_from_cache(self, city_name: str) -> Optional[Dict]:
        """Load cached data when available."""
        cache_path = self._get_cache_path(city_name)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def _save_to_cache(self, city_name: str, data: Dict):
        """Save data to cache."""
        cache_path = self._get_cache_path(city_name)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Errore salvataggio cache: {e}")
    
    def get_city_coordinates(self, city_name: str) -> Optional[Dict]:
        """
        Get coordinates for an Italian city.
		
        Returns:
            {'lat': float, 'lon': float, 'display_name': str} or None
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
        Get POIs for a city, with caching.
		
        Args:
            city_name: City name
            radius: Search radius in meters (default 15 km)
			
        Returns:
            List of POIs with name, type, rating, duration, cost, categories, lat, lon
        """
        # Check cache
        cached_data = self._load_from_cache(city_name)
        if cached_data:
            print(f"  💾 Cache hit per {city_name}")
            return cached_data.get('pois', [])
        
        print(f"  🌐 Interrogo OSM per {city_name}...")
        
        # Get city center coordinates
        coords = self.get_city_coordinates(city_name)
        if not coords:
            print(f"  ❌ Coordinate non trovate per {city_name}")
            return []
        
        lat, lon = coords['lat'], coords['lon']
        
        # Fetch POIs with retries for rate limiting
        pois = self._fetch_pois_with_retry(lat, lon, radius)
        
        # Convert OSM POIs to the local database format
        formatted_pois = self._format_pois(pois)
        
        # Curate to max 20 POIs with diversity
        curated_pois = self._select_diverse_pois(formatted_pois, max_pois=20, min_per_category=2)
        
        # Save to cache
        cache_data = {
            'city': city_name,
            'coordinates': coords,
            'pois': curated_pois,
            'fetched_at': datetime.now().isoformat(),
            'radius': radius,
            'total_pois_found': len(formatted_pois),
            'curated_count': len(curated_pois)
        }
        self._save_to_cache(city_name, cache_data)
        
        return curated_pois
    
    def _fetch_pois_with_retry(self, lat: float, lon: float, radius: int, max_retries: int = 3) -> List[Dict]:
        """
        Fetch POIs from OSM with error handling and retries.
        """
        # Simpler query to reduce timeouts
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
                    # Too many requests, wait longer
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
        Convert OSM POIs to the local database format.
        """
        formatted = []
        
        for poi in osm_pois:
            tags = poi.get("tags", {})
            name = tags.get("name")
            
            if not name or name == "Unnamed":
                continue
            
            # Determine the primary type
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
            
            # Estimate rating using available tags
            rating = self._estimate_rating(tags)
            
            formatted_poi = {
                "name": name,
                "rating": rating,
                "duration_hours": self._estimate_duration(poi_type),
                "cost": self._estimate_cost(poi_type),
                "categories": categories,
                "lat": poi.get("lat"),
                "lon": poi.get("lon"),
                "popularity": rating,  # Use rating as a proxy
                "osm_id": poi.get("id"),
                "osm_type": poi_type
            }
            
            formatted.append(formatted_poi)
        
        return formatted
    
    def _map_osm_category(self, osm_tag: str) -> str:
        """Map OSM tags to local categories."""
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
        """Estimate a rating based on available tag data."""
        # Wikipedia or Wikidata usually indicates relevance
        if tags.get("wikipedia") or tags.get("wikidata"):
            return 8.0
        
        # UNESCO heritage tag
        if tags.get("heritage"):
            return 9.0
        
        # Default
        return 7.0
    
    def _estimate_duration(self, poi_type: str) -> float:
        """Estimate visit duration based on POI type."""
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
        """Estimate cost based on POI type."""
        costs = {
            "museum": 12.0,
            "gallery": 10.0,
            "castle": 15.0,
            "monument": 5.0,
            "park": 0.0,
            "attraction": 10.0
        }
        return costs.get(poi_type, 8.0)    
    def _select_diverse_pois(self, pois: List[Dict], max_pois: int = 20, min_per_category: int = 2) -> List[Dict]:
        """
        Select diverse POIs while balancing categories and ratings.

        Strategy
        1) Limit to max_pois (default 20)
        2) Ensure min_per_category for each target category (natura, cultura, arte, cibo, mare, montagna, storia, sport)
        3) Balance ratings to avoid selecting only the highest scores
        4) Prefer higher rated items while keeping variety
        """
        if len(pois) <= max_pois:
            return pois
        
        # Target categories we want to ensure diversity
        target_categories = ['natura', 'cultura', 'arte', 'cibo', 'mare', 'montagna', 'storia', 'sport']
        
        # Organize POIs by category
        by_category = {cat: [] for cat in target_categories}
        other_pois = []
        
        for poi in pois:
            poi_cats = poi.get('categories', [])
            matched = False
            for cat in target_categories:
                if cat in poi_cats:
                    by_category[cat].append(poi)
                    matched = True
                    break
            if not matched:
                other_pois.append(poi)
        
        # Sort each category by rating
        for cat in target_categories:
            by_category[cat].sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        selected = []
        
        # Phase 1: Ensure min_per_category for each category (if available)
        for cat in target_categories:
            if by_category[cat]:
                # For each category, take 1 top-rated and 1 mid-range for variety
                if len(by_category[cat]) >= min_per_category:
                    # Top rated
                    selected.append(by_category[cat][0])
                    # Mid-range (around 60% down the list)
                    mid_idx = min(len(by_category[cat]) - 1, len(by_category[cat]) // 2)
                    if mid_idx > 0:
                        selected.append(by_category[cat][mid_idx])
                    # Mark as used
                    by_category[cat] = by_category[cat][1:mid_idx] + by_category[cat][mid_idx+1:]
                else:
                    # Take what we have
                    selected.extend(by_category[cat][:min_per_category])
                    by_category[cat] = by_category[cat][min_per_category:]
        
        # Phase 2: Fill remaining slots with best available, ensuring rating diversity
        remaining_slots = max_pois - len(selected)
        
        if remaining_slots > 0:
            # Collect remaining POIs
            remaining = []
            for cat in target_categories:
                remaining.extend(by_category[cat])
            remaining.extend(other_pois)
            
            # Sort by rating
            remaining.sort(key=lambda x: x.get('rating', 0), reverse=True)
            
            # Take mix: 60% from top half, 40% from mid-range
            top_count = int(remaining_slots * 0.6)
            mid_count = remaining_slots - top_count
            
            # Top rated
            selected.extend(remaining[:top_count])
            
            # Mid-range for variety
            if len(remaining) > top_count:
                mid_start = len(remaining) // 3  # Start from 1/3 down
                mid_pois = remaining[mid_start:mid_start + mid_count]
                selected.extend(mid_pois)
        
        return selected[:max_pois]    
    def get_train_station(self, city_name: str) -> Optional[Dict]:
        """
        Find the city's main train station.
        """
        self._rate_limit()
        
        # Try common station name variants
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
                
                # Filter for railway/station-like results
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
            
            time.sleep(0.5)  # Short pause between queries
        
        return None


# Test
if __name__ == "__main__":
    provider = OSMProvider()
    
    print("🧪 Test OSM Provider\n")
    
    # Test cities not present in the static database
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
        
        # Station
        station = provider.get_train_station(city)
        if station:
            print(f"\n🚂 Stazione: {station['name']}")
