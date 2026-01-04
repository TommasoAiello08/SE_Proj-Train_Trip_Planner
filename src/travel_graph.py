"""
Travel Graph Builder
Costruisce un grafo delle connessioni tra città usando API Trenitalia
Calcola tempi e costi di viaggio tra le città
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
import sys

# Aggiungi src al path per import
sys.path.insert(0, str(Path(__file__).parent))

from apitr import apitr
from city_database import CityDatabase
import time

class TravelGraph:
    """Grafo delle connessioni ferroviarie tra città"""
    
    def __init__(self, cache_file: str = None):
        self.api = apitr(decodeJson=True)
        self.city_db = CityDatabase()
        
        if cache_file is None:
            # Default: cerca in cache/ relativo alla root del progetto
            cache_file = Path(__file__).parent.parent / "cache" / "travel_graph_cache.json"
        self.cache_file = Path(cache_file)
        self.graph = {}
        
        # Carica cache se esiste
        self.load_cache()
    
    def load_cache(self):
        """Carica grafo da cache"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                self.graph = json.load(f)
            print(f"✅ Grafo caricato da cache: {len(self.graph)} città")
        else:
            print("ℹ️  Nessuna cache trovata, sarà creata al primo utilizzo")
    
    def save_cache(self):
        """Salva grafo su cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.graph, f, indent=2)
        print(f"💾 Cache salvata: {self.cache_file}")
    
    def estimate_travel_time(self, origin: str, destination: str) -> Optional[float]:
        """
        Stima tempo di viaggio tra due città (in ore)
        Usa cache se disponibile, altrimenti chiama API
        """
        # Controlla cache
        if origin in self.graph:
            if destination in self.graph[origin]:
                cached = self.graph[origin][destination]
                return cached.get('avg_time_hours')
        
        # Altrimenti calcola (simulato per ora - richiede API call)
        return self._calculate_travel_time_api(origin, destination)
    
    def _calculate_travel_time_api(self, origin: str, destination: str) -> Optional[float]:
        """
        Calcola tempo reale usando API Trenitalia
        
        Nota: Per 4 giorni, usa stime hardcoded o cache.
        Per versione completa, interroga API per ogni coppia.
        """
        # TODO: Implementare chiamata API reale
        # Per ora usa distanza geografica come proxy
        
        origin_city = self.city_db.get_city_by_name(origin)
        dest_city = self.city_db.get_city_by_name(destination)
        
        if not origin_city or not dest_city:
            return None
        
        # Calcola distanza in linea d'aria
        from math import radians, cos, sin, asin, sqrt
        
        coords = origin_city.get("coordinates")
        if not coords or "lat" not in coords or "lon" not in coords:
            raise ValueError(f"Missing coordinates for city '{origin}'")

        coords2 = dest_city.get("coordinates")
        if not coords2 or "lat" not in coords2 or "lon" not in coords2:
            raise ValueError(f"Missing coordinates for city '{destination}'")

        
        lat1, lon1 = origin_city['coordinates']['lat'], origin_city['coordinates']['lon']
        lat2, lon2 = dest_city['coordinates']['lat'], dest_city['coordinates']['lon']
        
        # Haversine
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance_km = 6371 * c
        
        # Stima tempo: velocità media treni ~100 km/h + buffer
        estimated_hours = (distance_km / 100) + 0.5
        
        return round(estimated_hours, 2)
    
    def build_complete_graph(self, force_rebuild: bool = False):
        """
        Costruisce grafo completo con tutte le connessioni
        
        Args:
            force_rebuild: Se True, ricalcola anche se esiste cache
        """
        if self.graph and not force_rebuild:
            print("✅ Grafo già presente in cache")
            return
        
        print("🔨 Costruzione grafo delle connessioni...")
        cities = self.city_db.get_all_cities()
        
        for origin_city in cities:
            origin_name = origin_city['name']
            self.graph[origin_name] = {}
            
            for dest_city in cities:
                if dest_city['name'] == origin_name:
                    continue
                
                dest_name = dest_city['name']
                
                # Calcola tempo
                travel_time = self.estimate_travel_time(origin_name, dest_name)
                
                if travel_time:
                    self.graph[origin_name][dest_name] = {
                        'avg_time_hours': travel_time,
                        'distance_km': self._calculate_distance(origin_city, dest_city),
                        'origin_station': origin_city['station_code'],
                        'dest_station': dest_city['station_code']
                    }
            
            print(f"  ✓ {origin_name}: {len(self.graph[origin_name])} connessioni")
        
        # Salva cache
        self.save_cache()
        print(f"✅ Grafo completo: {len(self.graph)} città")
    
    def _calculate_distance(self, city1: Dict, city2: Dict) -> float:
        """Calcola distanza geografica tra due città"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1 = city1['coordinates']['lat']
        lon1 = city1['coordinates']['lon']
        lat2 = city2['coordinates']['lat']
        lon2 = city2['coordinates']['lon']
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return round(6371 * c, 1)
    
    def get_reachable_cities(self, origin: str, max_hours: float = 4.0) -> List[Dict]:
        """
        Trova città raggiungibili da origin entro max_hours
        
        Returns:
            Lista di dict con {city, travel_time, distance}
        """
        if origin not in self.graph:
            print(f"⚠️  {origin} non trovata nel grafo")
            return []
        
        reachable = []
        for dest, info in self.graph[origin].items():
            if info['avg_time_hours'] <= max_hours:
                dest_city = self.city_db.get_city_by_name(dest)
                reachable.append({
                    'city': dest,
                    'city_data': dest_city,
                    'travel_time_hours': info['avg_time_hours'],
                    'distance_km': info['distance_km']
                })
        
        # Ordina per tempo di viaggio
        reachable.sort(key=lambda x: x['travel_time_hours'])
        return reachable
    
    def find_shortest_path(self, origin: str, destination: str) -> Optional[List[str]]:
        """
        Trova il percorso più breve tra due città (Dijkstra)
        
        Returns:
            Lista di città nel percorso, oppure None
        """
        if origin not in self.graph or destination not in self.graph:
            return None
        
        # Dijkstra's algorithm
        import heapq
        
        distances = {city: float('inf') for city in self.graph}
        distances[origin] = 0
        previous = {city: None for city in self.graph}
        pq = [(0, origin)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == destination:
                break
            
            for neighbor, info in self.graph[current].items():
                if neighbor in visited:
                    continue
                
                distance = current_dist + info['avg_time_hours']
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        # Ricostruisci percorso
        if distances[destination] == float('inf'):
            return None
        
        path = []
        current = destination
        while current is not None:
            path.append(current)
            current = previous[current]
        
        return list(reversed(path))
    
    def get_connection_details(self, origin: str, destination: str) -> Optional[Dict]:
        """Ottieni dettagli connessione tra due città"""
        if origin in self.graph and destination in self.graph[origin]:
            return self.graph[origin][destination]
        return None
    
    def visualize_connections(self, city: str):
        """Stampa connessioni di una città"""
        if city not in self.graph:
            print(f"❌ {city} non trovata")
            return
        
        print(f"\n🚂 CONNESSIONI DA {city}")
        print("="*60)
        
        connections = sorted(
            self.graph[city].items(),
            key=lambda x: x[1]['avg_time_hours']
        )
        
        for dest, info in connections:
            hours = info['avg_time_hours']
            mins = int((hours % 1) * 60)
            print(f"  → {dest:20s}  {int(hours)}h {mins:02d}m  ({info['distance_km']} km)")


def demo_travel_graph():
    """Demo del grafo di viaggio"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          Travel Graph Demo                              ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    graph = TravelGraph()
    
    # Costruisci grafo (usa cache se esiste)
    graph.build_complete_graph()
    
    # Test 1: Città raggiungibili
    print("\n\n1️⃣  CITTÀ RAGGIUNGIBILI DA MILANO (max 3 ore)")
    print("─"*60)
    reachable = graph.get_reachable_cities("Milano", max_hours=3.0)
    for entry in reachable:
        hours = entry['travel_time_hours']
        mins = int((hours % 1) * 60)
        print(f"  • {entry['city']:15s}  {int(hours)}h {mins:02d}m  ({entry['distance_km']} km)")
    
    # Test 2: Percorso più breve
    print("\n\n2️⃣  PERCORSO PIÙ BREVE: Bologna → Napoli")
    print("─"*60)
    path = graph.find_shortest_path("Bologna", "Napoli")
    if path:
        print(f"  Percorso: {' → '.join(path)}")
        
        total_time = 0
        for i in range(len(path) - 1):
            details = graph.get_connection_details(path[i], path[i+1])
            if details:
                total_time += details['avg_time_hours']
                print(f"  {path[i]} → {path[i+1]}: {details['avg_time_hours']}h")
        print(f"\n  Total time: {total_time:.2f} ore")
    
    # Test 3: Connessioni da una città
    print("\n\n3️⃣  TUTTE LE CONNESSIONI DA FIRENZE")
    graph.visualize_connections("Firenze")
    
    # Test 4: Matrice distanze (prime 5 città)
    print("\n\n4️⃣  MATRICE TEMPI DI VIAGGIO (ore)")
    print("─"*60)
    cities = ["Milano", "Roma", "Firenze", "Venezia", "Napoli"]
    
    # Header
    print(f"{'':12s}", end="")
    for city in cities:
        print(f"{city[:8]:>10s}", end="")
    print()
    
    # Righe
    for origin in cities:
        print(f"{origin[:12]:12s}", end="")
        for dest in cities:
            if origin == dest:
                print(f"{'---':>10s}", end="")
            else:
                details = graph.get_connection_details(origin, dest)
                if details:
                    time_str = f"{details['avg_time_hours']:.1f}h"
                    print(f"{time_str:>10s}", end="")
                else:
                    print(f"{'N/A':>10s}", end="")
        print()
    
    print("\n" + "="*60)
    print("✅ Demo completata!")


if __name__ == "__main__":
    demo_travel_graph()
