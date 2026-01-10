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
        self.MIN_STAY_HOURS = 2  # Reduced from 3 - più flessibilità per viaggi lunghi
        self.MAX_TRAIN_HOURS_PER_DAY = 12  # Increased from 10 - permette tratte più lunghe
        self.MAX_DAYS_PER_CITY = 2  # Max giorni consecutivi per città
        self.MAX_CANDIDATES = 35  # Increased from 30 - more cities for long routes
        self.MAX_CONNECTIONS_PER_CITY = 12  # Increased from 8 - explore more routes to reach distant cities
        self.TRAIN_BUFFER_HOURS = 1.0  # Buffer per accesso stazione
        
        # Cache
        self.train_cache = {}  # (origin_code, dest_code, date) -> train_info

        # ViaggiaTreno caches to reduce request volume (avoids throttling during matrix build)
        self._vt_station_cache: Dict[str, Optional[Dict]] = {}
        self._vt_departures_cache: Dict[Tuple[str, str], Optional[List[Dict]]] = {}
    
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

        # Candidate selection: small and fairly stable.
        t_candidates = 0.5

        # Train matrix dominates wall-clock time.
        # With the ViaggiaTreno strategy we typically do:
        # - ~1 `partenze` call per origin/day
        # - some `andamentoTreno` calls for promising departures
        # The real runtime is usually ~1–2 minutes, so be conservative.
        departure_calls = min(self.MAX_CANDIDATES * num_days, 80)
        total_pairs = self.MAX_CANDIDATES * self.MAX_CONNECTIONS_PER_CITY * num_days
        andamento_calls = min(int(total_pairs * 0.25), 180)
        num_api_calls = int(departure_calls + andamento_calls)

        # Rough per-call costs + fixed overhead (network + JSON + Python processing)
        t_train_matrix = (departure_calls * 0.35) + (andamento_calls * 0.35) + 8.0

        # DP + schedule generation
        t_dp = max(0.7, num_days * 0.25)
        t_details = num_days * 0.2

        total = t_candidates + t_train_matrix + t_dp + t_details

        return {
            'candidate_selection': t_candidates,
            'train_matrix': t_train_matrix,
            'dp_optimization': t_dp,
            'detail_generation': t_details,
            'total_estimated': total,
            'num_api_calls': num_api_calls,
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
            trip_input.days,
            trip_input.end_city  # Pass end city to ensure it's always reachable
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
        - ISLAND RESTRICTION: Sardinia stays isolated (no trains to mainland)
        """
        # Define island cities - NO trains to mainland Italy!
        sardinian_cities = {'Cagliari', 'Sassari', 'Nuoro', 'Oristano'}
        
        # Check if start is in Sardinia
        start_in_sardinia = start in sardinian_cities
        
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
            
            # CRITICAL: If trip starts in Sardinia, ONLY consider Sardinian cities
            # (no trains connect Sardinia to mainland - ferry only)
            city_in_sardinia = city_name in sardinian_cities
            
            if start_in_sardinia and not city_in_sardinia:
                # Skip mainland cities if starting from Sardinia
                continue
            elif not start_in_sardinia and city_in_sardinia:
                # Skip Sardinian cities if starting from mainland
                continue
            
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
                
                # Bonus for cities along the route based on reasonable travel
                # PROXIMITY IS KING: Nearby cities strongly preferred, but big cities still attractive
                
                # For open trips (start == end), use distance from start only
                if start == end:
                    # Exponential proximity bonus - closer cities get MUCH more weight
                    if dist_from_start < 100:
                        route_bonus = 450  # Very close (within region) - MASSIVE boost
                    elif dist_from_start < 200:
                        route_bonus = 320  # Nearby regions - major boost
                    elif dist_from_start < 350:
                        route_bonus = 170  # Same-day reachable
                    elif dist_from_start < 500:
                        route_bonus = 50   # Long day trip
                    elif dist_from_start < 700:
                        route_bonus = 0    # Very far - no bonus
                    else:
                        route_bonus = -100  # Too far - strong penalty!
                else:
                    # For point-to-point trips: bonus for cities ON the route
                    # If dist_from_start + dist_from_end ≈ total_distance, city is on path
                    detour = (dist_from_start + dist_from_end) - total_distance
                    if detour < 50:  # On the direct route
                        route_bonus = 320
                    elif detour < 150:  # Minor detour
                        route_bonus = 200
                    elif detour < 300:  # Moderate detour
                        route_bonus = 100
                    else:  # Major detour
                        route_bonus = 0
                
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
        Score provincia basato su attrazioni, interessi, e importanza città
        Balanced scoring without proximity (handled separately)
        """
        attractions = city_data.get('attractions', [])
        if not attractions:
            return 0.0
        
        # City importance rating (1-10: major cities get higher score)
        city_importance = city_data.get('importance', 5.0)
        
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
        
        # Rebalanced formula: proximity matters MORE, importance gives "gravitational pull"
        # City importance now gives smaller boost to allow smaller cities to compete
        score = (
            category_match * 12 +  # Interest matching
            len(attractions) * 0.4 +  # Number of attractions (slightly higher)
            avg_rating * 2.5 +  # Quality (slightly higher)
            avg_popularity * 0.6 +  # Popularity (slightly higher)
            city_importance * 12  # Importance: 12-120 points (reduced from 18-180)
        )
        
        return score
    
    def _select_relevant_destinations(
        self,
        origin: str,
        candidates: List[str],
        max_dests: int,
        force_include: List[str] = None
    ) -> List[str]:
        """
        Seleziona le destinazioni più rilevanti per una città origine
        (riduce numero chiamate API)
        
        Criteri:
        - Distanza geografica (preferenza vicini)
        - Score provincia (preferenza più interessanti)
        - force_include: città da includere sempre (es. destinazione finale)
        """
        origin_data = self.city_db.get_city_by_name(origin)
        if not origin_data:
            return candidates[:max_dests]
        
        force_include = force_include or []
        
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
        
        # CRITICAL FIX: Ensure force_include cities are ALWAYS included first
        # This guarantees that the destination is always reachable from any origin
        selected = []
        
        # First, add all force_include cities (except origin itself)
        for city in force_include:
            if city != origin and city in candidates:
                selected.append(city)
        
        # Then, add top-scoring cities until we reach max_dests
        for dest, _ in scored_dests:
            if dest not in selected:
                selected.append(dest)
                if len(selected) >= max_dests:
                    break
        
        return selected
    
    def _build_train_matrix(
        self,
        candidates: List[str],
        start_date: datetime,
        num_days: int,
        end: str
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
            # Prefer morning departures (09:00-11:00) for all days
            search_hour = 9
            current_date = start_date + timedelta(days=day - 1)
            current_datetime = current_date.replace(hour=search_hour, minute=0, second=0)
            print(f"  📅 Giorno {day} ({current_datetime.strftime('%Y-%m-%d %H:%M')})")

            # IMPORTANT: ViaggiaTreno station endpoints (partenze/andamento) are live feeds but can
            # provide departures for near-future dates (e.g., tomorrow). We therefore query the
            # actual itinerary day at 09:00 to prefer morning trains. If the requested datetime is
            # in the past for today, the train lookup layer will fall back to a near-now query.
            schedule_datetime = current_date.replace(hour=search_hour, minute=0, second=0, microsecond=0)
            if schedule_datetime.hour < 8:
                schedule_datetime = schedule_datetime.replace(hour=8, minute=0)
            
            # Per ogni città di origine
            for origin in candidates:
                train_matrix[day][origin] = {}
                
                # OTTIMIZZAZIONE: per ogni origine, considera solo le MAX_CONNECTIONS_PER_CITY
                # destinazioni più vicine/rilevanti (riduce chiamate API)
                # IMPORTANTE: Sempre includere destinazione finale per garantire percorso valido
                candidate_dests = self._select_relevant_destinations(
                    origin,
                    candidates,
                    self.MAX_CONNECTIONS_PER_CITY,
                    force_include=[end]  # Ensure end city is always reachable
                )
                
                for dest in candidate_dests:
                    if origin == dest:
                        continue
                    
                    # Cerca treno migliore per questa coppia
                    train_info = self._find_best_train(
                        origin,
                        dest,
                        schedule_datetime
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
        # Controlla cache (include time-of-day to avoid reusing a morning train for afternoon searches)
        cache_key = (origin_city, dest_city, date.strftime('%Y-%m-%d %H:%M'))
        if cache_key in self.train_cache:
            return self.train_cache[cache_key]
        
        # Ottieni città dal database
        origin_data = self.city_db.get_city_by_name(origin_city)
        dest_data = self.city_db.get_city_by_name(dest_city)
        
        if not origin_data or not dest_data:
            return None
        
        try:
            # NOTE: ViaggiaTreno "soluzioniViaggioNew" is frequently unavailable (404).
            # Use working endpoints: station departures + train status.
            train_info = self._find_best_train_from_departures(origin_city, dest_city, date)
            if train_info:
                self.train_cache[cache_key] = train_info
                return train_info
        except Exception as e:
            print(f"    ⚠️  API error {origin_city}->{dest_city}: {e}")

        # Fallback: stima geometrica
        return self._estimate_train_connection(origin_data, dest_data)

    def _find_best_train_from_departures(self, origin_city: str, dest_city: str, date: datetime) -> Optional[Dict]:
        """Find a plausible direct train using ViaggiaTreno `partenze` + `andamentoTreno`.

        Constraints:
        - departure time must be >= 08:00
        - ViaggiaTreno does not provide ticket prices; price is estimated
        """
        origin_station = self._pick_viaggiatreno_station(origin_city)
        dest_station = self._pick_viaggiatreno_station(dest_city)
        if not origin_station or not dest_station:
            return None

        origin_data = self.city_db.get_city_by_name(origin_city)
        dest_data = self.city_db.get_city_by_name(dest_city)

        # Enforce departure after 08:00
        preferred_dt = date.replace(second=0, microsecond=0)
        if preferred_dt.hour < 8:
            preferred_dt = preferred_dt.replace(hour=8, minute=0)

        # Build a list of query times: try preferred time first, then (if needed) fall back to near-now.
        search_dts = [preferred_dt]
        now = datetime.now().replace(second=0, microsecond=0)
        if preferred_dt.date() == now.date() and preferred_dt < now:
            # Round up to next 5 minutes
            minute = (now.minute + 4) // 5 * 5
            if minute >= 60:
                now = now.replace(hour=min(now.hour + 1, 23), minute=0)
            else:
                now = now.replace(minute=minute)
            if now.hour < 8:
                now = now.replace(hour=8, minute=0)
            if now != preferred_dt:
                search_dts.append(now)

        departures = None
        search_dt = None
        for candidate_dt in search_dts:
            dep_cache_key = (str(origin_station['id']), candidate_dt.strftime('%Y-%m-%d %H:%M'))
            if dep_cache_key in self._vt_departures_cache:
                departures = self._vt_departures_cache[dep_cache_key]
            else:
                raw_departures = self.api_treni.getPartenze(origin_station['id'], candidate_dt)
                departures = raw_departures if isinstance(raw_departures, list) else None
                # Cache even None to avoid hammering when the endpoint is temporarily failing
                self._vt_departures_cache[dep_cache_key] = departures

            if departures and isinstance(departures, list):
                search_dt = candidate_dt
                break

        if not departures or not isinstance(departures, list) or search_dt is None:
            return None

        dest_upper = str(dest_station.get('nomeLungo') or dest_station.get('nomeBreve') or '').strip().upper()
        if not dest_upper:
            return None

        # Collect direct candidates to the requested destination
        candidates = []
        for item in departures:
            if not isinstance(item, dict):
                continue
            if str(item.get('destinazione', '')).strip().upper() != dest_upper:
                continue
            numero_treno = item.get('numeroTreno')
            dep_hhmm = item.get('orarioPartenza')
            if not numero_treno or not dep_hhmm:
                continue
            candidates.append((str(numero_treno).strip(), str(dep_hhmm).strip(), item))

        if not candidates:
            return None

        # Prefer departures between 09:00 and 11:00 when available.
        preferred_start_min = 9 * 60
        preferred_end_min = 11 * 60
        target_min = 10 * 60  # aim for ~10:00

        enriched = []
        for numero_treno, dep_hhmm, raw in candidates:
            dep_dt = self._combine_date_hhmm(search_dt, dep_hhmm)
            dep_min = dep_dt.hour * 60 + dep_dt.minute
            in_window = preferred_start_min <= dep_min < preferred_end_min
            enriched.append((in_window, dep_min, numero_treno, dep_hhmm, raw, dep_dt))

        # Keep deterministic order by departure time
        preferred = sorted([c for c in enriched if c[0]], key=lambda x: x[1])
        others = sorted([c for c in enriched if not c[0]], key=lambda x: x[1])

        def probe(group):
            best_info_local = None
            best_score_local = None
            # Limit remote calls
            for in_window, dep_min, numero_treno, dep_hhmm, raw, dep_dt in group[:6]:
                andamento = self.api_treni.getAndamento(origin_station['id'], numero_treno, dep_dt)
                duration_h = None
                dep_str = None
                arr_str = None

                if andamento and isinstance(andamento, dict):
                    durata = andamento.get('compDurata')
                    if durata:
                        parsed = self._parse_duration(str(durata))
                        if parsed and parsed > 0:
                            duration_h = parsed
                    dep_str = andamento.get('compOrarioPartenza')
                    arr_str = andamento.get('compOrarioArrivo')

                # For future dates, `andamentoTreno` may be unavailable; estimate duration/arrival.
                if duration_h is None:
                    distance_km = self._haversine_km(origin_data, dest_data)
                    train_class = self._classify_train(numero_treno, raw.get('categoriaDescrizione') or raw.get('categoria') or raw.get('tipoTreno'))
                    if train_class == 'alta_velocita':
                        speed_kmh, overhead = 180.0, 0.4
                    elif train_class == 'intercity':
                        speed_kmh, overhead = 120.0, 0.7
                    elif train_class == 'diurni_internazionali':
                        speed_kmh, overhead = 130.0, 0.8
                    else:
                        speed_kmh, overhead = 80.0, 0.9
                    if distance_km > 0:
                        duration_h = max(0.5, (distance_km / speed_kmh) + overhead)
                    else:
                        duration_h = 3.0
                    dep_str = dep_str or dep_dt.strftime('%H:%M')
                    from datetime import timedelta
                    arr_dt = dep_dt + timedelta(minutes=int(duration_h * 60))
                    arr_str = arr_str or arr_dt.strftime('%H:%M')

                categoria = raw.get('categoriaDescrizione') or raw.get('categoria') or raw.get('tipoTreno')
                train_label = f"{categoria} {numero_treno}".strip() if categoria else f"{numero_treno}"

                price_est = self._estimate_ticket_price(origin_city, dest_city, numero_treno, categoria)

                info = {
                    'train': train_label,
                    'travel_time': round(duration_h, 2),
                    'departure': dep_str or dep_hhmm,
                    'arrival': arr_str,
                    'price': price_est,
                    'price_estimated': True,
                    'changes': 0,
                    'numero_treno': numero_treno,
                    'estimated': False
                }

                # In preferred window: choose closest to target time, then shortest duration.
                # Outside window: choose shortest duration.
                if in_window:
                    score = (abs(dep_min - target_min), duration_h)
                else:
                    score = (duration_h,)

                if best_score_local is None or score < best_score_local:
                    best_score_local = score
                    best_info_local = info

            return best_info_local

        # Try preferred window first, then fall back.
        best_info = probe(preferred) if preferred else None
        if best_info:
            return best_info
        return probe(others)

    def _estimate_ticket_price(
        self,
        origin_city: str,
        dest_city: str,
        numero_treno: Optional[str],
        categoria: Optional[str] = None,
    ) -> float:
        """Estimate ticket price (1 adult) based on distance and train type.

        Train-type rules (by train number):
        - Regionale: all numbers not listed below
        - Intercity (servizio interno): 500-999
        - Diurni internazionali: 1-199
        - Alta velocità (servizio interno): 8000-8999 and 9300-9999

        If the number cannot be parsed, fall back to category name.
        """
        origin_data = self.city_db.get_city_by_name(origin_city)
        dest_data = self.city_db.get_city_by_name(dest_city)
        distance_km = self._haversine_km(origin_data, dest_data)
        if distance_km <= 0:
            # Reasonable fallback
            return 25.0

        train_class = self._classify_train(numero_treno, categoria)

        # €/km rates + base fees (tuned to be plausible, not exact)
        if train_class == 'regionale':
            base, rate = 4.0, 0.06
        elif train_class == 'intercity':
            base, rate = 7.0, 0.09
        elif train_class == 'diurni_internazionali':
            base, rate = 8.0, 0.11
        elif train_class == 'alta_velocita':
            base, rate = 12.0, 0.17
        else:
            base, rate = 6.0, 0.08

        price = base + (distance_km * rate)

        # Clamp to sensible bounds
        price = max(base, price)
        price = min(price, 250.0)
        return round(price, 2)

    def _classify_train(self, numero_treno: Optional[str], categoria: Optional[str] = None) -> str:
        try:
            if numero_treno is not None:
                n = int(str(numero_treno).strip())
                if 500 <= n <= 999:
                    return 'intercity'
                if 1 <= n <= 199:
                    return 'diurni_internazionali'
                if (8000 <= n <= 8999) or (9300 <= n <= 9999):
                    return 'alta_velocita'
                return 'regionale'
        except Exception:
            pass

        cat = (categoria or '').upper()
        if 'INTERCITY' in cat or cat.startswith('IC'):
            return 'intercity'
        if 'FRECCIAROSSA' in cat or 'FRECCIARGENTO' in cat or 'FRECCIABIANCA' in cat or cat.startswith('FR'):
            return 'alta_velocita'
        return 'regionale'

    def _haversine_km(self, origin_data: Optional[Dict], dest_data: Optional[Dict]) -> float:
        try:
            if not origin_data or not dest_data:
                return 0.0
            o = origin_data.get('coordinates') or {}
            d = dest_data.get('coordinates') or {}
            lat1, lon1 = float(o.get('lat')), float(o.get('lon'))
            lat2, lon2 = float(d.get('lat')), float(d.get('lon'))

            from math import radians, cos, sin, asin, sqrt
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            return 6371.0 * c
        except Exception:
            return 0.0

    def _combine_date_hhmm(self, base_dt: datetime, hhmm: str) -> datetime:
        s = str(hhmm).strip()
        # ViaggiaTreno sometimes returns epoch timestamps (ms) instead of 'HH:MM'
        try:
            if s.isdigit():
                val = int(s)
                if val > 10**11:  # likely epoch milliseconds
                    return datetime.fromtimestamp(val / 1000.0)
                if val > 10**9:  # likely epoch seconds
                    return datetime.fromtimestamp(val)
        except Exception:
            pass

        try:
            parts = s.split(':')
            hh = int(parts[0])
            mm = int(parts[1])
            return base_dt.replace(hour=hh, minute=mm, second=0, microsecond=0)
        except Exception:
            return base_dt

    def _pick_viaggiatreno_station(self, query: str) -> Optional[Dict]:
        """Pick a likely main station for a city name using ViaggiaTreno station search."""
        q_norm = (query or '').strip().lower()
        if q_norm in self._vt_station_cache:
            return self._vt_station_cache[q_norm]

        results = self.api_treni.searchStazione(query)
        if not results:
            self._vt_station_cache[q_norm] = None
            return None
        if isinstance(results, dict):
            self._vt_station_cache[q_norm] = results
            return results
        if not isinstance(results, list):
            self._vt_station_cache[q_norm] = None
            return None

        q = q_norm

        # Prefer a "Centrale" station when available
        for st in results:
            name = str(st.get('nomeLungo', '')).lower()
            if 'centrale' in name and (q in name or q == ''):
                self._vt_station_cache[q_norm] = st
                return st

        # Otherwise prefer an exact nomeLungo match
        for st in results:
            if str(st.get('nomeLungo', '')).strip().lower() == q:
                self._vt_station_cache[q_norm] = st
                return st

        picked = results[0] if results else None
        self._vt_station_cache[q_norm] = picked
        return picked
    
    def _estimate_train_connection(
        self,
        origin_data: Dict,
        dest_data: Dict
    ) -> Dict:
        """
        Fallback: stima connessione ferroviaria da distanza geografica
        """
        from math import radians, cos, sin, asin, sqrt
        
        origin_name = origin_data.get('name', '')
        dest_name = dest_data.get('name', '')
        
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
        
        # Special handling for island routes
        sicilian_cities = {'Palermo', 'Catania', 'Messina', 'Siracusa', 'Agrigento', 'Trapani', 'Ragusa', 'Enna', 'Caltanissetta'}
        sardinian_cities = {'Cagliari', 'Sassari', 'Nuoro', 'Oristano'}
        mainland_cities = {'Roma', 'Milano', 'Napoli', 'Firenze', 'Torino', 'Bologna', 'Venezia', 'Genova', 'Verona'}
        
        # Sardinia: NO TRAIN SERVICE to mainland (ferry only - not supported)
        is_sardinia_crossing = (
            (origin_name in sardinian_cities and dest_name not in sardinian_cities) or
            (origin_name not in sardinian_cities and dest_name in sardinian_cities)
        )
        
        if is_sardinia_crossing:
            # Block completely - return impossibly high cost
            return {
                'train': None,
                'exists': False,
                'travel_time': 999.0,
                'price': 999999.0,
                'numero_treno': 'NO_SERVICE',
                'estimated': True
            }
        
        is_sicily_crossing = (
            (origin_name in sicilian_cities and dest_name in mainland_cities) or
            (origin_name in mainland_cities and dest_name in sicilian_cities)
        )
        
        # Stima tempo: velocità variabile basata su distanza
        # Treni regionali: ~80 km/h, IC: ~120 km/h, AV: ~180 km/h
        # Usa velocità conservativa per evitare sottostime
        if is_sicily_crossing:
            # Sicily-mainland: add ferry time + slower route
            avg_speed = 60  # Very slow due to ferry and connections
            estimated_hours = (distance_km / avg_speed) + 3.0  # +3h for ferry and transfers
        elif distance_km < 100:
            # Short distance - regional trains
            avg_speed = 80
            estimated_hours = (distance_km / avg_speed) + 0.5
        elif distance_km < 300:
            # Medium distance - intercity
            avg_speed = 100
            estimated_hours = (distance_km / avg_speed) + 0.8
        else:
            # Long distance - may require connections or slower routes
            avg_speed = 85  # Much slower for very long routes
            estimated_hours = (distance_km / avg_speed) + 1.5
        
        return {
            'train': None,
            'travel_time': round(estimated_hours, 2),
            'departure': '09:00',
            'arrival': f"{9 + int(estimated_hours):02d}:{int((estimated_hours % 1) * 60):02d}",
            'price': self._estimate_ticket_price(origin_name, dest_name, None, None),
            'price_estimated': True,
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
        print(f"  📍 Start: {start}, End: {end}, Days: {num_days}")
        print(f"  🌍 Candidates: {len(candidates)} cities")
        print(f"  🔍 Is {end} in candidates? {end in candidates}")
        if end not in candidates:
            print(f"  ⚠️  WARNING: Destination {end} NOT in candidate list!")
            print(f"  Candidates: {candidates}")
        
        # Inizializzazione
        dp = [{} for _ in range(num_days + 1)]
        prev = [{} for _ in range(num_days + 1)]
        visited_cities = [{} for _ in range(num_days + 1)]  # Track cities visited up to day d
        consecutive_days = [{} for _ in range(num_days + 1)]  # Track consecutive days in same city
        
        # dp[0][start] = score(start)
        start_score = self._calculate_province_score(
            self.city_db.get_city_by_name(start),
            interests
        )
        dp[1][start] = start_score
        prev[1][start] = None
        visited_cities[1][start] = {start}  # Start city is visited
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
        
        # Calculate how many unique cities we can realistically visit
        # If num_days > candidates, we MUST have 2-day stays
        max_unique_cities = len(candidates)
        need_multi_day_stays = num_days > max_unique_cities
        
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
                
                # Calculate remaining days after this move
                days_remaining = num_days - d
                cities_visited_count = len(visited_cities[d].get(A, {A}))
                cities_not_visited = max_unique_cities - cities_visited_count
                
                # Need 2-day stays if: remaining_days > cities_not_visited
                # This means we have more days left than unique cities available
                should_encourage_stays = days_remaining > cities_not_visited
                
                # Option 1: STAY in same city A for another day
                # Allow for cities with importance >= 7 (not just 8) when we need to fill days
                A_data = self.city_db.get_city_by_name(A)
                A_importance = A_data.get('importance', 5.0) if A_data else 5.0
                
                # Dynamic threshold: lower it when we need multi-day stays to fill itinerary
                # For small island regions (like Sardinia), we MUST allow stays even in smaller cities
                if need_multi_day_stays:
                    # If days > cities, we absolutely NEED multi-day stays
                    # Allow ANY city to have 2-day stays (importance >= 4.0)
                    importance_threshold = 4.0
                elif should_encourage_stays:
                    # If running out of cities, be flexible
                    importance_threshold = 6.0
                else:
                    # Normal case: only major cities get 2-day stays
                    importance_threshold = 8.0
                    
                is_major_city = A_importance >= importance_threshold
                
                # Calculate maximum days we can stay in one city
                # If we have more days than cities, we MUST allow 2+ day stays
                max_stay_days = 2  # Default: max 2 days per city
                if need_multi_day_stays:
                    # For islands like Sardinia: allow staying up to 3 days if needed
                    max_stay_days = 3
                
                if is_major_city and days_in_A < max_stay_days:
                    stay_reward = city_scores.get(A, 0.0) * 0.7
                    
                    # Bonus increases when we need stays to fill the itinerary
                    if should_encourage_stays:
                        stay_bonus = 50  # Higher bonus when we need to fill days
                    else:
                        stay_bonus = 30  # Normal bonus
                    
                    stay_score = dp[d][A] + stay_reward + stay_bonus
                    
                    if A not in dp[next_day] or stay_score > dp[next_day][A]:
                        dp[next_day][A] = stay_score
                        prev[next_day][A] = A  # Same city
                        visited_cities[next_day][A] = visited_cities[d][A].copy()  # Same visited set
                        consecutive_days[next_day][A] = days_in_A + 1
                        reason = "[NEED STAYS]" if should_encourage_stays else "[MAJOR CITY]"
                        print(f"    {A} -> {A} (stay day {days_in_A + 1}): score={stay_score:.2f} {reason}")
                elif not is_major_city:
                    print(f"    {A} -> {A} (stay): BLOCKED - not major enough (importance={A_importance:.1f}, need>={importance_threshold:.1f})")
                else:
                    print(f"    {A} -> {A} (stay): BLOCKED - already {days_in_A} days (max={max_stay_days})")
                
                # Option 2: MOVE to different city B
                # Prova tutte le destinazioni B
                for B in candidates:
                    if B == A:
                        continue
                    
                    # CRITICAL: Prevent revisiting cities already in the route
                    cities_visited_so_far = visited_cities[d].get(A, set())
                    if B in cities_visited_so_far:
                        continue  # Skip - already visited this city
                    
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
                    
                    # Travel penalty: scale exponentially for very long trips
                    # Short trips (<3h): light penalty
                    # Long trips (>5h): heavy penalty to discourage cross-country journeys
                    if travel_time < 3:
                        travel_penalty = travel_time * 5
                    elif travel_time < 5:
                        travel_penalty = travel_time * 10  # Moderate penalty
                    else:
                        travel_penalty = travel_time * 20  # Heavy penalty for very long trains
                    
                    # Update DP
                    new_score = dp[d][A] + reward_B + exploration_bonus - travel_penalty
                    
                    if B not in dp[next_day] or new_score > dp[next_day][B]:
                        dp[next_day][B] = new_score
                        prev[next_day][B] = A
                        # Add B to visited cities
                        new_visited = cities_visited_so_far.copy()
                        new_visited.add(B)
                        visited_cities[next_day][B] = new_visited
                        consecutive_days[next_day][B] = 1  # Reset to 1 when moving to new city
                        print(f"    {A} -> {B}: score={new_score:.2f} (travel={travel_time:.1f}h)")
        
        # Backtrack: trova percorso migliore che arriva a 'end'
        # IMPORTANT: For best experience, prefer using ALL available days
        # For open-ended trips (start == end), prefer ending at a DIFFERENT city
        best_day = -1
        best_score = float('-inf')
        best_end_city = end
        
        # Check if this is an open-ended trip (round trip)
        is_round_trip = (start == end)
        
        if is_round_trip:
            # For round trips, prefer ending at ANY city except start
            print(f"  🔄 Round trip detected - seeking diverse route (avoid returning to {start})")
            
            # CRITICAL: Must use ALL requested days
            # Find best city to end at on the FINAL day (excluding start city)
            for city in candidates:
                if city == start:
                    continue  # Skip start city
                
                if city in dp[num_days]:
                    score = dp[num_days][city]
                    if score > best_score:
                        best_score = score
                        best_day = num_days
                        best_end_city = city
            
            if best_day == num_days:
                print(f"  ✅ Found open route using ALL {num_days} days, ending at {best_end_city} (score: {best_score:.2f})")
            else:
                # ONLY fallback if absolutely no route found for final day
                # This should be very rare with our improved stay logic
                print(f"  ⚠️  WARNING: Could not fill all {num_days} days - checking earlier days...")
                for d in range(num_days - 1, 0, -1):
                    if not dp[d]:
                        continue
                    for city in candidates:
                        if city == start:
                            continue
                        if city in dp[d] and dp[d][city] > best_score:
                            best_score = dp[d][city]
                            best_day = d
                            best_end_city = city
                
                if best_day != -1:
                    print(f"  ⚠️  FALLBACK: Open route ends at {best_end_city} on day {best_day} (requested {num_days})")
                    print(f"  ℹ️  Consider requesting fewer days or selecting a different start city")
        else:
            # Fixed destination: MUST use all requested days
            # First, try to find path that uses all days to reach end city
            if end in dp[num_days]:
                best_day = num_days
                best_score = dp[num_days][end]
                best_end_city = end
                print(f"  ✅ Found route using all {num_days} days to reach {end}")
            else:
                # ONLY fallback if absolutely no route found
                print(f"  ⚠️  WARNING: Could not reach {end} in {num_days} days - checking earlier arrivals...")
                for d in range(num_days - 1, 0, -1):
                    if end in dp[d] and dp[d][end] > best_score:
                        best_score = dp[d][end]
                        best_day = d
                        best_end_city = end
                if best_day > 0:
                    print(f"  ⚠️  FALLBACK: Could only reach {end} in {best_day} days (requested {num_days})")
                    print(f"  ℹ️  Consider requesting fewer days or selecting intermediate destinations")
        
        # Update end to actual ending city
        end = best_end_city
        
        if best_day == -1:
            print("=" * 80, flush=True)
            print("🚨 FALLBACK TRIGGERED - DP FAILED TO FIND ROUTE 🚨", flush=True)
            print(f"  ⚠️  Nessun percorso trovato per {start} -> {end}", flush=True)
            print(f"  ℹ️  DEBUG: Checking DP states...", flush=True)
            for d in range(1, min(num_days + 1, 6)):
                if dp[d]:
                    cities = list(dp[d].keys())
                    print(f"    Day {d}: {len(cities)} cities reachable: {cities[:8]}", flush=True)
                    if end in cities:
                        print(f"      ✓ {end} is reachable on day {d}!", flush=True)
                else:
                    print(f"    Day {d}: NO CITIES REACHABLE", flush=True)
            
            print(f"  ℹ️  Checking if {end} ever appears in DP...", flush=True)
            end_found_days = []
            for d in range(1, num_days + 1):
                if end in dp[d]:
                    end_found_days.append(d)
            print(f"    {end} found on days: {end_found_days if end_found_days else 'NEVER - this is the problem!'}", flush=True)
            print("=" * 80, flush=True)
            
            # SMART FALLBACK: Find intermediate cities along the geographic route
            print(f"  ℹ️  Generating smart fallback route...", flush=True)
            
            # Get coordinates
            start_city_data = self.city_db.get_city_by_name(start)
            end_city_data = self.city_db.get_city_by_name(end)
            
            if start_city_data and end_city_data and num_days >= 5:
                # Find cities along the path
                from math import radians, cos, sin, asin, sqrt, atan2
                
                start_lat = start_city_data['coordinates']['lat']
                start_lon = start_city_data['coordinates']['lon']
                end_lat = end_city_data['coordinates']['lat']
                end_lon = end_city_data['coordinates']['lon']
                
                # Find cities that are between start and end
                intermediate_cities = []
                for city in candidates:
                    if city == start or city == end:
                        continue
                    
                    city_data = self.city_db.get_city_by_name(city)
                    if not city_data:
                        continue
                    
                    clat = city_data['coordinates']['lat']
                    clon = city_data['coordinates']['lon']
                    
                    # Distance to line start->end
                    # Use cross-track distance approximation
                    # If city is between start and end, use it
                    
                    # Distance from start to city
                    dlat = radians(clat - start_lat)
                    dlon = radians(clon - start_lon)
                    a = sin(dlat/2)**2 + cos(radians(start_lat)) * cos(radians(clat)) * sin(dlon/2)**2
                    dist_start_city = 2 * asin(sqrt(a)) * 6371
                    
                    # Distance from city to end
                    dlat = radians(end_lat - clat)
                    dlon = radians(end_lon - clon)
                    a = sin(dlat/2)**2 + cos(radians(clat)) * cos(radians(end_lat)) * sin(dlon/2)**2
                    dist_city_end = 2 * asin(sqrt(a)) * 6371
                    
                    # Distance start to end
                    dlat = radians(end_lat - start_lat)
                    dlon = radians(end_lon - start_lon)
                    a = sin(dlat/2)**2 + cos(radians(start_lat)) * cos(radians(end_lat)) * sin(dlon/2)**2
                    dist_start_end = 2 * asin(sqrt(a)) * 6371
                    
                    # If detour is small, city is on the route
                    detour = (dist_start_city + dist_city_end) - dist_start_end
                    
                    if detour < 150:  # Max 150km detour
                        intermediate_cities.append((city, dist_start_city))
                
                # Sort by distance from start
                intermediate_cities.sort(key=lambda x: x[1])
                
                # Build route: start (2 days) -> intermediate cities (respecting MAX_DAYS) -> end
                route = [start, start]  # Start with 2 days at start (respects MAX_DAYS_PER_CITY=2)
                days_used = 2
                
                for city, _ in intermediate_cities:
                    if days_used >= num_days - 1:  # Leave at least 1 day for end
                        break
                    days_to_add = min(self.MAX_DAYS_PER_CITY, num_days - days_used - 1)
                    route.extend([city] * days_to_add)
                    days_used += days_to_add
                
                # Fill remaining days with end city
                remaining_days = num_days - days_used
                route.extend([end] * remaining_days)
                
                print(f"  ✅ Smart fallback generated: {route}", flush=True)
                print(f"  ℹ️  Intermediate cities: {[c for c, _ in intermediate_cities[:3]]}", flush=True)
            else:
                # Simple fallback for short trips or missing data
                if num_days <= 2:
                    route = [start] + [end]
                elif num_days == 3:
                    route = [start, start, end]
                elif num_days == 4:
                    route = [start, start, end, end]
                else:  # 5+ days
                    route = [start, start, end, end, end][:num_days]
                print(f"  ℹ️  Using simple fallback route: {route}", flush=True)
            
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
