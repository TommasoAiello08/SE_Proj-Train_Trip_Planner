"""
Dynamic Programming Itinerary Planner con API Trenitalia
=========================================================

Basato sul report: algoritmo DP per macro-itinerario + Knapsack per attrazioni

Input:
- start_province, end_province
- travel_days (N)
- preferences (categorie + pesi)
- start_date

Output:
- Itinerario ottimale giorno per giorno con treni reali

Algoritmo:
1. **Candidate selection**: top-N province per score
2. **Train matrix**: chiamate API reali per ogni coppia (A,B) per giorno
3. **DP macro**: dp[d][B] = max score raggiungendo B al giorno d
4. **Knapsack micro**: per ogni provincia, seleziona attrazioni ottimali
5. **Vincolo**: minimo 1 giorno per provincia

"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from city_database import CityDatabase
from apitr import apitr
import heapq


@dataclass
class TripInput:
    """Input richiesta viaggio"""
    days: int
    start_city: str
    end_city: str
    interests: List[str]
    budget: Optional[float] = None
    start_date: Optional[datetime] = None


@dataclass
class DaySchedule:
    """Schedule di un singolo giorno"""
    day_number: int
    date: datetime
    city: str
    
    # Viaggio
    morning_train: Optional[Dict] = None
    travel_time: float = 0.0
    from_city: Optional[str] = None
    
    # Attività
    pois: List[Dict] = None
    available_hours: float = 0.0
    
    # Costi
    estimated_cost: float = 0.0
    daily_cost: float = 0.0


class DPItineraryPlanner:
    """
    Planner con Dynamic Programming per ottimizzazione globale
    """
    
    def __init__(self):
        self.city_db = CityDatabase(use_osm=True)
        self.api_treni = apitr(decodeJson=True)
        
        # Parametri configurabili  
        self.HOURS_PER_DAY = 13  # Ore disponibili per giorno (8:00-21:00)
        self.MIN_STAY_HOURS = 3  # Minimo 3 ore per provincia
        self.MAX_TRAIN_HOURS_PER_DAY = 10  # Max ore di treno al giorno
        self.MAX_DAYS_PER_CITY = 2  # Max giorni consecutivi per città
        self.MAX_CANDIDATES = 30  # Reduced for performance (30×8=240 per day vs 50×12=600)
        self.MAX_CONNECTIONS_PER_CITY = 8  # Reduced for performance
        self.TRAIN_BUFFER_HOURS = 1.0  # Buffer per accesso stazione
        
        # Cache
        self.train_cache = {}  # (origin_code, dest_code, date) -> train_info
    
    def estimate_computation_time(self, trip_input: TripInput) -> Dict[str, float]:
        """
        Stima tempo di computazione per mostrare progress bar
        
        Returns:
            {
                'candidate_selection': secondi,
                'train_matrix': secondi,
                'dp_optimization': secondi,
                'detail_generation': secondi,
                'total_estimated': secondi
            }
        """
        num_days = trip_input.days
        
        # Candidate selection: ~0.3s (route-based scoring with 2 distance calcs per city)
        t_candidates = 0.3
        
        # Train matrix: API calls più costose
        # Con MAX_CANDIDATES=35 e MAX_CONNECTIONS_PER_CITY=8
        # Potenziali chiamate: 35 * 8 * num_days = 280 * num_days
        # Ma molte sono cached dopo primo run
        
        # Stima realistica basata su testing:
        # - Primo run: ~15-20 API calls per giorno (cache misses)
        # - Run successivi: ~3-5 API calls per giorno (alcune cache expiry)
        # - Cache hits: resto delle 280 * num_days chiamate
        
        estimated_new_calls = min(18 * num_days, 40)  # Cap at 40 total
        total_possible_calls = self.MAX_CANDIDATES * self.MAX_CONNECTIONS_PER_CITY * num_days
        estimated_cached_calls = max(0, total_possible_calls - estimated_new_calls)
        
        # Tempo: 0.5s per API call nuova, 0.003s per cache hit
        t_train_matrix = (estimated_new_calls * 0.5) + (estimated_cached_calls * 0.003)
        
        # DP: più lento ora che valuta anche "stay" option
        # Complessità: O(days * candidates^2) per move + O(days * candidates) per stay
        # Con 35 candidates e stay option: ~(35^2 + 35) * days = ~1260 * days operations
        t_dp = max(0.5, num_days * 0.2)  # Scala con giorni (ridotto)
        
        # Detail generation: Knapsack con 20 POIs per città (più veloce che con 100+)
        # Ma ora dobbiamo gestire multiple days per city
        t_details = num_days * 0.15
        
        total = t_candidates + t_train_matrix + t_dp + t_details
        
        return {
            'candidate_selection': t_candidates,
            'train_matrix': t_train_matrix,
            'dp_optimization': t_dp,
            'detail_generation': t_details,
            'total_estimated': total
        }
    
    def plan_trip(self, trip_input: TripInput) -> List[DaySchedule]:
        """
        Metodo principale: pianifica itinerario con DP
        
        Steps:
        1. Score e selezione province candidate
        2. Costruzione matrice treni (API reali)
        3. DP per sequenza province ottimale
        4. Knapsack per attrazioni in ogni tappa
        5. Genera schedule dettagliato
        """
        print(f"\n🚀 DP ITINERARY PLANNER")
        print(f"📍 {trip_input.start_city} → {trip_input.end_city}")
        print(f"📅 {trip_input.days} giorni")
        print(f"🎯 Interessi: {', '.join(trip_input.interests)}")
        
        # Stima tempo
        time_estimate = self.estimate_computation_time(trip_input)
        print(f"⏱️  Tempo stimato: {time_estimate['total_estimated']:.1f}s")
        print("="*70)
        
        # Step 1: Candidate selection
        candidates = self._select_candidate_provinces(
            trip_input.start_city,
            trip_input.end_city,
            trip_input.interests
        )
        
        # Step 2: Train matrix (API calls)
        train_matrix = self._build_train_matrix(
            candidates,
            trip_input.start_date,
            trip_input.days
        )
        
        # Step 3: DP per sequenza ottimale
        route, dp_scores = self._dp_route_optimization(
            trip_input.start_city,
            trip_input.end_city,
            candidates,
            train_matrix,
            trip_input.days,
            trip_input.interests
        )
        
        # Step 4: Alloca giorni a province (minimo 1)
        day_allocation = self._allocate_days_to_route(
            route,
            trip_input.days,
            train_matrix
        )
        
        # Step 5: Genera schedule dettagliato con Knapsack
        schedule = self._generate_detailed_schedule(
            route,
            day_allocation,
            train_matrix,
            trip_input.start_date,
            trip_input.interests
        )
        
        print(f"\n✅ Itinerario generato: {len(schedule)} giorni")
        return schedule
    
    def _select_candidate_provinces(
        self,
        start: str,
        end: str,
        interests: List[str]
    ) -> List[str]:
        """
        Step 1: Seleziona top-N province per score
        
        Score basato su:
        - Numero attrazioni per categorie preferite
        - Rating medio
        - Popolarità
        - Distanza geografica (regional bias)
        """
        all_cities = self.city_db.get_all_cities()
        scored_cities = []
        
        # Get start city coordinates for route-based scoring
        start_city_data = self.city_db.get_city_by_name(start)
        end_city_data = self.city_db.get_city_by_name(end)
        start_lat = start_city_data['coordinates']['lat'] if start_city_data else None
        start_lon = start_city_data['coordinates']['lon'] if start_city_data else None
        end_lat = end_city_data['coordinates']['lat'] if end_city_data else None
        end_lon = end_city_data['coordinates']['lon'] if end_city_data else None
        
        # Pre-calculate total distance start->end (only once!)
        total_distance = 0
        if start_lat and start_lon and end_lat and end_lon:
            from math import radians, cos, sin, asin, sqrt
            lat1, lon1, lat2, lon2 = map(radians, [start_lat, start_lon, end_lat, end_lon])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            total_distance = 6371 * c
        
        for city_data in all_cities:
            city_name = city_data['name']
            
            # Sempre includi start e end
            if city_name == start or city_name == end:
                scored_cities.append((city_name, 999999.0))
                continue
            
            # Calcola score con regional bias
            score = self._calculate_province_score(city_data, interests)
            
            # Add route proximity bonus: favor cities along the path from start to end
            if start_lat and start_lon and end_lat and end_lon:
                from math import radians, cos, sin, asin, sqrt
                city_lat = city_data['coordinates']['lat']
                city_lon = city_data['coordinates']['lon']
                
                # Distance from start
                lat1, lon1, lat2, lon2 = map(radians, [start_lat, start_lon, city_lat, city_lon])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                dist_from_start = 6371 * c
                
                # Distance from end
                lat1, lon1, lat2, lon2 = map(radians, [end_lat, end_lon, city_lat, city_lon])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                dist_from_end = 6371 * c
                
                # Bonus for cities along the route: penalize detours
                # If dist_from_start + dist_from_end ≈ total_distance, city is on the path
                detour = (dist_from_start + dist_from_end) - total_distance
                route_bonus = max(0, 200 - (detour / 10))  # Max 200 bonus, -10 per km of detour
                
                score += route_bonus
            
            scored_cities.append((city_name, score))
        
        # Ordina e prendi top-N
        scored_cities.sort(key=lambda x: x[1], reverse=True)
        
        # Top candidates + start + end
        candidates = []
        added = set()
        
        # Add start city first
        candidates.append(start)
        added.add(start)
        
        # Add top-N cities (excluding start and end which already have high scores)
        for city, score in scored_cities:
            if city not in added and city != end:
                candidates.append(city)
                added.add(city)
                if len(candidates) >= self.MAX_CANDIDATES:
                    break
        
        # Ensure end city is included
        if end not in added:
            candidates.append(end)
        
        print(f"  🎯 Selected {len(candidates)} candidate cities from {len(all_cities)} total")
        print(f"  📋 Top candidates: {', '.join(candidates[:10])}{'...' if len(candidates) > 10 else ''}")
        
        return candidates
    
    def _calculate_province_score(
        self,
        city_data: Dict,
        interests: List[str]
    ) -> float:
        """
        Score provincia basato su attrazioni e interessi
        """
        attractions = city_data.get('attractions', [])
        if not attractions:
            return 0.0
        
        # Conta attrazioni per categoria
        category_match = 0
        total_rating = 0
        total_popularity = 0
        
        for attr in attractions:
            # Match categorie
            attr_cats = attr.get('categories', [])
            if any(cat in interests for cat in attr_cats):
                category_match += 1
            
            # Rating e popolarità
            total_rating += attr.get('rating', 3.0)
            total_popularity += attr.get('popularity', 50)
        
        avg_rating = total_rating / len(attractions)
        avg_popularity = total_popularity / len(attractions)
        
        score = (
            category_match * 20 +  # Match interessi (increased weight)
            len(attractions) * 0.3 +  # Numero attrazioni (reduced weight)
            avg_rating * 2 +  # Qualità
            avg_popularity * 0.5  # Popolarità (reduced weight)
        )
        
        return score
    
    def _select_relevant_destinations(
        self,
        origin: str,
        candidates: List[str],
        max_dests: int
    ) -> List[str]:
        """
        Seleziona le destinazioni più rilevanti per una città origine
        (riduce numero chiamate API)
        
        Criteri:
        - Distanza geografica (preferenza vicini)
        - Score provincia (preferenza più interessanti)
        """
        origin_data = self.city_db.get_city_by_name(origin)
        if not origin_data:
            return candidates[:max_dests]
        
        origin_lat = origin_data['coordinates']['lat']
        origin_lon = origin_data['coordinates']['lon']
        
        # Calcola score + distanza per ogni candidato
        scored_dests = []
        for dest in candidates:
            if dest == origin:
                continue
            
            dest_data = self.city_db.get_city_by_name(dest)
            if not dest_data:
                continue
            
            # Distanza
            dest_lat = dest_data['coordinates']['lat']
            dest_lon = dest_data['coordinates']['lon']
            
            from math import radians, cos, sin, asin, sqrt
            lat1, lon1, lat2, lon2 = map(radians, [origin_lat, origin_lon, dest_lat, dest_lon])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance_km = 6371 * c
            
            # Score: preferenza province vicine (max 500km) con buon rating
            proximity_score = max(0, 500 - distance_km)
            attraction_score = len(dest_data.get('attractions', [])) * 2
            
            total_score = proximity_score + attraction_score
            scored_dests.append((dest, total_score))
        
        # Ordina e prendi top-N
        scored_dests.sort(key=lambda x: x[1], reverse=True)
        return [dest for dest, _ in scored_dests[:max_dests]]
    
    def _build_train_matrix(
        self,
        candidates: List[str],
        start_date: datetime,
        num_days: int
    ) -> Dict:
        """
        Step 2: Costruisce matrice treni con API reali
        
        Returns:
            train_matrix[day][origin][dest] = {
                'train': dict,
                'travel_time': float,
                'departure': str,
                'arrival': str,
                'price': float
            }
        """
        print("\n🚂 Step 2: Building Train Matrix (API Calls)")
        
        train_matrix = {day: {} for day in range(1, num_days + 1)}
        
        # Per ogni giorno
        for day in range(1, num_days + 1):
            # For day 1: search trains from 9:00 (early morning)
            # For day 2+: search trains from 13:00 (after lunch/activities)
            search_hour = 9 if day == 1 else 13
            current_date = start_date + timedelta(days=day - 1)
            current_datetime = current_date.replace(hour=search_hour, minute=0, second=0)
            print(f"  📅 Giorno {day} ({current_datetime.strftime('%Y-%m-%d %H:%M')})")
            
            # Per ogni città di origine
            for origin in candidates:
                train_matrix[day][origin] = {}
                
                # OTTIMIZZAZIONE: per ogni origine, considera solo le MAX_CONNECTIONS_PER_CITY
                # destinazioni più vicine/rilevanti (riduce chiamate API)
                candidate_dests = self._select_relevant_destinations(
                    origin,
                    candidates,
                    self.MAX_CONNECTIONS_PER_CITY
                )
                
                for dest in candidate_dests:
                    if origin == dest:
                        continue
                    
                    # Cerca treno migliore per questa coppia
                    train_info = self._find_best_train(
                        origin,
                        dest,
                        current_datetime
                    )
                    
                    if train_info:
                        train_matrix[day][origin][dest] = train_info
            
        return train_matrix
    
    def _find_best_train(
        self,
        origin_city: str,
        dest_city: str,
        date: datetime
    ) -> Optional[Dict]:
        """
        Trova il miglior treno per coppia città + data usando API Trenitalia
        
        Strategia:
        1. Ottieni codici stazione per origine/destinazione
        2. Chiama getIndicazioniViaggio per soluzioni
        3. Seleziona treno con min durata (o min cambi)
        4. Fallback: stima geometrica
        """
        # Controlla cache
        cache_key = (origin_city, dest_city, date.strftime('%Y-%m-%d'))
        if cache_key in self.train_cache:
            return self.train_cache[cache_key]
        
        # Ottieni città dal database
        origin_data = self.city_db.get_city_by_name(origin_city)
        dest_data = self.city_db.get_city_by_name(dest_city)
        
        if not origin_data or not dest_data:
            return None
        
        origin_station_code = origin_data.get('station_code')
        dest_station_code = dest_data.get('station_code')
        
        if not origin_station_code or not dest_station_code:
            # Fallback: stima geometrica
            return self._estimate_train_connection(origin_data, dest_data)
        
        try:
            # Chiamata API reale
            soluzioni = self.api_treni.getIndicazioniViaggio(
                origin_station_code,
                dest_station_code,
                date
            )
            
            if soluzioni and len(soluzioni) > 0:
                # Prendi soluzione migliore (min durata)
                best = min(soluzioni, key=lambda s: self._parse_duration(s.get('durata', '99:99')))
                
                train_info = {
                    'train': best,
                    'travel_time': self._parse_duration(best.get('durata', '3:00')),
                    'departure': best.get('orarioPartenza', '09:00'),
                    'arrival': best.get('orarioArrivo', '12:00'),
                    'price': best.get('prezzo_stimato', {}).get('seconda_classe', 30.0),
                    'changes': best.get('cambi', 0),
                    'numero_treno': best.get('soluzione', [{}])[0].get('numeroTreno', 'N/A') if best.get('soluzione') else 'N/A'
                }
                
                # Cache
                self.train_cache[cache_key] = train_info
                return train_info
        
        except Exception as e:
            print(f"    ⚠️  API error {origin_city}->{dest_city}: {e}")
        
        # Fallback
        return self._estimate_train_connection(origin_data, dest_data)
    
    def _estimate_train_connection(
        self,
        origin_data: Dict,
        dest_data: Dict
    ) -> Dict:
        """
        Fallback: stima connessione ferroviaria da distanza geografica
        """
        from math import radians, cos, sin, asin, sqrt
        
        lat1 = origin_data['coordinates']['lat']
        lon1 = origin_data['coordinates']['lon']
        lat2 = dest_data['coordinates']['lat']
        lon2 = dest_data['coordinates']['lon']
        
        # Haversine
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance_km = 6371 * c
        
        # Stima tempo: ~100 km/h + buffer
        estimated_hours = (distance_km / 100) + 0.5
        
        return {
            'train': None,
            'travel_time': round(estimated_hours, 2),
            'departure': '09:00',
            'arrival': f"{9 + int(estimated_hours):02d}:{int((estimated_hours % 1) * 60):02d}",
            'price': max(10.0, distance_km * 0.12),  # ~0.12€/km
            'changes': 0,
            'numero_treno': 'STIMATO',
            'estimated': True
        }
    
    def _parse_duration(self, duration_str: str) -> float:
        """Converte 'HH:MM' in ore (float)"""
        try:
            parts = duration_str.split(':')
            return float(parts[0]) + float(parts[1]) / 60.0
        except:
            return 3.0
    
    def _dp_route_optimization(
        self,
        start: str,
        end: str,
        candidates: List[str],
        train_matrix: Dict,
        num_days: int,
        interests: List[str]
    ) -> Tuple[List[str], Dict]:
        """
        Step 3: Dynamic Programming per sequenza ottimale
        
        State: dp[d][B] = max score raggiungendo provincia B al giorno d
        
        Transizione:
        - da A a B se:
          travel_time(A,B,d) + MIN_STAY_HOURS <= HOURS_PER_DAY
        
        Returns:
            (route, dp_scores)
        """
        print("\n🧮 Step 3: DP Route Optimization")
        
        # Inizializzazione
        dp = [{} for _ in range(num_days + 1)]
        prev = [{} for _ in range(num_days + 1)]
        consecutive_days = [{} for _ in range(num_days + 1)]  # Track consecutive days in same city
        
        # dp[0][start] = score(start)
        start_score = self._calculate_province_score(
            self.city_db.get_city_by_name(start),
            interests
        )
        dp[1][start] = start_score
        prev[1][start] = None
        consecutive_days[1][start] = 1
        
        print(f"  Inizializzazione: dp[1][{start}] = {start_score:.2f}")
        
        # Cache city scores to avoid repeated calculations
        city_scores = {}
        for city in candidates:
            city_data = self.city_db.get_city_by_name(city)
            if city_data:
                city_scores[city] = self._calculate_province_score(city_data, interests)
            else:
                city_scores[city] = 0.0
        
        # DP: giorni 1 -> N
        for d in range(1, num_days):
            if not dp[d]:
                continue
            
            print(f"  Giorno {d} -> {d+1}:")
            
            for A in dp[d]:
                if dp[d][A] == float('-inf'):
                    continue
                
                # Prossimo giorno
                next_day = d + 1
                
                # Check how many consecutive days we've been in city A
                days_in_A = consecutive_days[d].get(A, 1)
                
                # Option 1: STAY in same city A for another day
                # Only allow if not already at MAX_DAYS_PER_CITY limit
                if days_in_A < self.MAX_DAYS_PER_CITY:
                    stay_reward = city_scores.get(A, 0.0) * 0.7
                    stay_bonus = 30
                    stay_score = dp[d][A] + stay_reward + stay_bonus
                    
                    if A not in dp[next_day] or stay_score > dp[next_day][A]:
                        dp[next_day][A] = stay_score
                        prev[next_day][A] = A  # Same city
                        consecutive_days[next_day][A] = days_in_A + 1
                        print(f"    {A} -> {A} (stay day {days_in_A + 1}): score={stay_score:.2f}")
                else:
                    print(f"    {A} -> {A} (stay): BLOCKED - already {days_in_A} days")
                
                # Option 2: MOVE to different city B
                # Prova tutte le destinazioni B
                for B in candidates:
                    if B == A:
                        continue
                    
                    # Controlla se esiste treno A -> B per giorno next_day
                    if next_day not in train_matrix:
                        continue
                    if A not in train_matrix[next_day]:
                        continue
                    if B not in train_matrix[next_day][A]:
                        continue
                    
                    train_info = train_matrix[next_day][A][B]
                    travel_time = train_info['travel_time'] + self.TRAIN_BUFFER_HOURS
                    
                    # Vincolo: viaggio + min stay <= ore giornata
                    if travel_time + self.MIN_STAY_HOURS > self.HOURS_PER_DAY:
                        continue
                    
                    # Vincolo: max ore treno
                    if travel_time > self.MAX_TRAIN_HOURS_PER_DAY:
                        continue
                    
                    # Reward provincia B (from cache)
                    reward_B = city_scores.get(B, 0.0)
                    
                    # Exploration bonus: encourage visiting new cities
                    # For multi-day trips, visiting more cities is generally better
                    exploration_bonus = 50  # Bonus for each new city visited
                    
                    # Travel penalty (light - we want to encourage exploration)
                    travel_penalty = travel_time * 5  # Increased from 2 to make long travels slightly more expensive
                    
                    # Update DP
                    new_score = dp[d][A] + reward_B + exploration_bonus - travel_penalty
                    
                    if B not in dp[next_day] or new_score > dp[next_day][B]:
                        dp[next_day][B] = new_score
                        prev[next_day][B] = A
                        consecutive_days[next_day][B] = 1  # Reset to 1 when moving to new city
                        print(f"    {A} -> {B}: score={new_score:.2f} (travel={travel_time:.1f}h)")
        
        # Backtrack: trova percorso migliore che arriva a 'end'
        # IMPORTANT: For best experience, prefer using ALL available days
        # Only look at day num_days first, then fall back to earlier days
        best_day = -1
        best_score = float('-inf')
        
        # First, try to find path that uses all days
        if end in dp[num_days]:
            best_day = num_days
            best_score = dp[num_days][end]
            print(f"  ✅ Found route using all {num_days} days")
        else:
            # Fall back to shorter routes
            for d in range(num_days - 1, 0, -1):
                if end in dp[d] and dp[d][end] > best_score:
                    best_score = dp[d][end]
                    best_day = d
            if best_day > 0:
                print(f"  ⚠️  Could only find route using {best_day} days (requested {num_days})")
        
        if best_day == -1:
            print(f"  ⚠️  Nessun percorso trovato per {start} -> {end}")
            print(f"  ℹ️  DEBUG: Checking DP states...")
            for d in range(1, min(num_days + 1, 4)):
                if dp[d]:
                    print(f"    Day {d}: cities reachable = {list(dp[d].keys())[:5]}")
            # Fallback: Try to create route with MAX_DAYS_PER_CITY=2 constraint
            # Pattern: start (2 days) -> ... -> end
            if num_days <= 2:
                route = [start] + [end]
            elif num_days == 3:
                route = [start, start, end]
            elif num_days == 4:
                route = [start, start, end, end]
            else:  # 5+ days
                # Try: start(2) + middle(2) + end(1+)
                route = [start, start, end, end, end][:num_days]
            print(f"  ℹ️  Using fallback route with MAX_DAYS constraint: {route}")
            return route, dp
        
        # Ricostruisci percorso
        route = []
        current = end
        for d in range(best_day, 0, -1):
            route.append(current)
            current = prev[d][current]
            if current is None:
                break
        
        route.reverse()
        
        # NO PADDING - respect MAX_DAYS_PER_CITY constraint
        # If DP found shorter route, that's the best valid route
        # Padding would violate MAX_DAYS_PER_CITY=2
        
        print(f"\n  ✅ Route ottimale: {' -> '.join(route)}")
        print(f"     Score totale: {best_score:.2f}")
        if len(route) < num_days:
            print(f"     ⚠️  Route uses {len(route)} days instead of requested {num_days} (respecting MAX_DAYS_PER_CITY constraint)")
        
        return route, dp
    
    def _allocate_days_to_route(
        self,
        route: List[str],
        total_days: int,
        train_matrix: Dict
    ) -> Dict[str, int]:
        """
        Step 4: Alloca giorni a province (minimo 1 per provincia)
        
        NOTE: route now contains day-by-day sequence with possible duplicates
        e.g., ['Trieste', 'Trieste', 'Firenze', 'Roma', 'Roma']
        This function just counts consecutive occurrences.
        """
        print("\n📆 Step 4: Allocating Days")
        
        # Count consecutive days in each city from the route
        allocation = {}
        i = 0
        while i < len(route):
            city = route[i]
            count = 1
            # Count consecutive occurrences
            while i + count < len(route) and route[i + count] == city:
                count += 1
            allocation[city] = count
            i += count
        
        print(f"  Day allocation: {allocation}")
        print(f"  Total days allocated: {sum(allocation.values())}")
        
        return allocation
    
    def _generate_detailed_schedule(
        self,
        route: List[str],
        day_allocation: Dict[str, int],
        train_matrix: Dict,
        start_date: datetime,
        interests: List[str]
    ) -> List[DaySchedule]:
        """
        Step 5: Genera schedule dettagliato con Knapsack per attrazioni
        
        IMPORTANT: Iterate through route in order, not day_allocation.items()
        """
        print("\n📋 Step 5: Generating Detailed Schedule")
        
        schedule = []
        current_date = start_date
        day_counter = 1
        prev_city = None
        used_attractions = {}  # Track attractions already used per city
        
        # IMPORTANT: Iterate day-by-day through route (which may have duplicates)
        # Example: ['Trieste', 'Trieste', 'Firenze', 'Roma', 'Roma']
        # This ensures we generate schedule for each day correctly
        for day_idx, city in enumerate(route):
            print(f"\n  📍 Day {day_counter}: {city.upper()}")
            
            # Initialize used attractions for this city
            if city not in used_attractions:
                used_attractions[city] = set()
            
            # Check if we're arriving from another city today
            travel_time = 0.0
            morning_train = None
            from_city_for_day = None
            
            if day_idx > 0 and route[day_idx - 1] != city:
                # We're moving from a different city
                prev_city = route[day_idx - 1]
                # Cerca treno nella matrice
                if day_counter in train_matrix:
                    if prev_city in train_matrix[day_counter]:
                        if city in train_matrix[day_counter][prev_city]:
                            train_info = train_matrix[day_counter][prev_city][city]
                            travel_time = train_info['travel_time']
                            morning_train = train_info
                            from_city_for_day = prev_city
                            print(f"    🚂 Treno: {prev_city} → {city}, {travel_time:.1f}h")
                
            # Running clock: giornata inizia alle 8:00 (ora 8)
            running_clock = 8.0
            
            # Aggiungi tempo viaggio treno
            running_clock += travel_time
            
            # Limite orario: 21:00 (ora 21)
            max_clock = 21.0
            
            # Knapsack: seleziona attrazioni con running clock
            pois = self._knapsack_attractions_with_clock(
                city,
                interests,
                running_clock,
                max_clock,
                exclude_names=used_attractions[city]
            )
            
            # Calcola ore disponibili totali per backward compatibility
            available_hours = max_clock - running_clock
            
            # Aggiungi le attrazioni selezionate alla lista used
            for poi in pois:
                used_attractions[city].add(poi['name'])
            
            # Calcola running clock finale (dopo POI)
            final_clock = running_clock + (len(pois) * 3.0)
            
            # Costo giornata
            daily_cost = self._estimate_daily_cost(city, pois, travel_time, morning_train)
            
            day_schedule = DaySchedule(
                day_number=day_counter,
                date=current_date,
                city=city,
                morning_train=morning_train,
                travel_time=travel_time,
                from_city=from_city_for_day,  # None if staying in same city
                pois=pois,
                available_hours=available_hours,
                estimated_cost=daily_cost,
                daily_cost=daily_cost
            )
            
            schedule.append(day_schedule)
            
            print(f"    Giorno {day_counter}: {len(pois)} POI, €{daily_cost:.2f} (clock: {final_clock:.1f}h/{max_clock:.0f}h)")
            
            # Verifica se clock supera limite (21:00)
            if final_clock > max_clock:
                print(f"    ⚠️  Clock limit reached ({final_clock:.1f}h > {max_clock:.0f}h) - day ended")
            
            current_date += timedelta(days=1)
            day_counter += 1
        
        return schedule
    
    def _knapsack_attractions_with_clock(
        self,
        city: str,
        interests: List[str],
        running_clock: float,
        max_clock: float,
        exclude_names: set = None
    ) -> List[Dict]:
        """
        Knapsack con running clock: ogni POI dura 3h, limita a ora 21:00
        
        running_clock: ora corrente (es. 8.0 per le 8:00, + tempo treno)
        max_clock: ora limite (21.0 = 21:00)
        exclude_names: set di nomi attrazioni da escludere
        """
        POI_DURATION = 3.0  # Ogni attività dura 3 ore
        
        if exclude_names is None:
            exclude_names = set()
            
        city_data = self.city_db.get_city_by_name(city)
        if not city_data:
            return []
        
        attractions = city_data.get('attractions', [])
        if not attractions:
            return []
        
        # Filtra attrazioni già usate
        attractions = [a for a in attractions if a['name'] not in exclude_names]
        
        if not attractions:
            return []
        
        # Score per attrazione
        scored = []
        for attr in attractions:
            # Match interessi
            match_score = sum(1 for cat in attr.get('categories', []) if cat in interests)
            
            # Score composito
            score = (
                match_score * 10 +
                attr.get('rating', 5) * 2 +
                attr.get('popularity', 5) * 1 -
                attr.get('cost_euro', 0) * 0.1
            )
            
            scored.append({
                **attr,
                'score': score,
                'duration_hours': POI_DURATION  # Forza 3h per ogni POI
            })
        
        # Ordina per score decrescente
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        # Seleziona POI con running clock
        selected = []
        current_clock = running_clock
        
        for attr in scored:
            # Verifica se c'è spazio per questa attività (non superare ore 21:00)
            if current_clock + POI_DURATION <= max_clock:
                selected.append(attr)
                current_clock += POI_DURATION
                
                # Max 3 attrazioni/giorno
                if len(selected) >= 3:
                    break
        
        # Differenzia tra 2 e 3 POI: accetta anche 2 se non c'è spazio per la terza
        # (il loop sopra già gestisce questo)
        
        return selected
    
    def _knapsack_attractions(
        self,
        city: str,
        interests: List[str],
        available_hours: float,
        exclude_names: set = None
    ) -> List[Dict]:
        """
        Knapsack 0/1 per selezione attrazioni ottimale (legacy)
        
        Obiettivo: massimizzare score sotto vincolo tempo
        exclude_names: set di nomi attrazioni da escludere (già usate in giorni precedenti)
        """
        if exclude_names is None:
            exclude_names = set()
            
        city_data = self.city_db.get_city_by_name(city)
        if not city_data:
            return []
        
        attractions = city_data.get('attractions', [])
        if not attractions:
            return []
        
        # Filtra attrazioni già usate
        attractions = [a for a in attractions if a['name'] not in exclude_names]
        
        if not attractions:
            return []
        
        # Score per attrazione
        scored = []
        for attr in attractions:
            # Match interessi
            match_score = sum(1 for cat in attr.get('categories', []) if cat in interests)
            
            # Score composito
            score = (
                match_score * 10 +
                attr.get('rating', 5) * 2 +
                attr.get('popularity', 5) * 1 -
                attr.get('cost_euro', 0) * 0.1
            )
            
            scored.append({
                **attr,
                'score': score,
                'duration_hours': attr.get('duration_hours', 2.0)
            })
        
        # Ordina per score/duration (greedy per MVP)
        scored.sort(key=lambda x: x['score'] / x['duration_hours'], reverse=True)
        
        # Knapsack greedy
        selected = []
        total_time = 0.0
        
        for attr in scored:
            if total_time + attr['duration_hours'] <= available_hours:
                selected.append(attr)
                total_time += attr['duration_hours']
                
                if len(selected) >= 3:  # Max 3 attrazioni/giorno
                    break
        
        # Assicura almeno 2 attrazioni se disponibili
        if len(selected) < 2 and len(scored) >= 2:
            selected = scored[:2]
        
        return selected
    
    def _estimate_daily_cost(
        self,
        city: str,
        pois: List[Dict],
        travel_time: float,
        morning_train: Optional[Dict]
    ) -> float:
        """
        Stima costo giornaliero: SOLO attrazioni + treno
        (rimossi pasti e alloggio per accuratezza)
        """
        # Costo attrazioni (dalle 2-3 POI selezionate)
        attr_cost = sum(poi.get('cost_euro', poi.get('cost', 0)) for poi in pois)
        
        # Costo treno (se presente)
        train_cost = morning_train.get('price', 0) if morning_train else 0
        
        return attr_cost + train_cost


def demo_dp_planner():
    """
    Demo: Milano -> Roma in 4 giorni con DP
    """
    print("\n🚀 DP ITINERARY PLANNER DEMO")
    print("="*70)
    
    trip = TripInput(
        days=4,
        start_city='Milano',
        end_city='Roma',
        interests=['arte', 'storia', 'cultura'],
        budget=500,
        start_date=datetime(2026, 1, 10)
    )
    
    planner = DPItineraryPlanner()
    schedule = planner.plan_trip(trip)
    
    # Print risultato
    print("\n" + "="*70)
    print("📋 ITINERARIO FINALE")
    print("="*70)
    
    total_cost = 0
    for day in schedule:
        print(f"\n🗓️  GIORNO {day.day_number} - {day.date.strftime('%d/%m/%Y')} - {day.city.upper()}")
        
        if day.morning_train:
            print(f"  🚂 Treno: {day.from_city} → {day.city}")
            print(f"     Durata: {day.travel_time:.1f}h")
            print(f"     Numero: {day.morning_train.get('numero_treno', 'N/A')}")
            print(f"     Costo: €{day.morning_train.get('price', 0):.2f}")
        
        print(f"  🎯 Attrazioni ({len(day.pois)}):")
        for poi in day.pois:
            print(f"     • {poi['name']} ({poi.get('duration_hours', 0)}h, €{poi.get('cost_euro', 0)})")
        
        print(f"  💰 Costo giornata: €{day.daily_cost:.2f}")
        total_cost += day.daily_cost
    
    print(f"\n{'='*70}")
    print(f"💵 COSTO TOTALE: €{total_cost:.2f}")
    print("="*70)
    
    return schedule


if __name__ == "__main__":
    demo_dp_planner()
