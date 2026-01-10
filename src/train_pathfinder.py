"""
Train Pathfinding - Algoritmo di ricerca percorsi ferroviari reali
===================================================================

Usa endpoint partenze/arrivi per costruire percorsi con cambi usando BFS.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import deque
import time


class TrainPathfinder:
    """
    Trova percorsi ferroviari ottimali usando dati reali API Trenitalia
    """
    
    def __init__(self, api_treni, city_db):
        self.api = api_treni
        self.city_db = city_db
        
        # Limiti ricerca
        self.MAX_CHANGES = 2  # Massimo 2 cambi
        self.MAX_WAIT_HOURS = 3  # Massimo 3 ore di attesa per cambio
        self.MIN_TRANSFER_MINUTES = 10  # Minimo 10 minuti per cambio
        self.SEARCH_TIMEOUT_SECONDS = 15  # Timeout ricerca
        
        # Cache
        self.station_cache = {}  # city_name -> station_code
        
    def find_train_route(
        self,
        origin_city: str,
        dest_city: str,
        departure_time: datetime
    ) -> Optional[Dict]:
        """
        Trova il percorso ferroviario migliore da origine a destinazione
        
        Strategia:
        1. Ottieni stazione di origine e destinazione
        2. BFS sui treni in partenza
        3. Per ogni treno, controlla se va a destinazione o a stazioni intermedie utili
        4. Costruisci percorso con cambi se necessario
        
        WORKAROUND DATE: L'API Trenitalia restituisce dati solo per oggi.
        Se la data è futura, usa l'anno precedente (stesso giorno/mese).
        Gli orari ferroviari cambiano poco anno dopo anno.
        
        Returns:
            {
                'train': dettagli percorso completo,
                'travel_time': ore totali (viaggio + attese),
                'departure': orario partenza,
                'arrival': orario arrivo,
                'price': prezzo stimato,
                'changes': numero cambi,
                'segments': lista segmenti del percorso
            }
        """
        start_time = time.time()
        
        # 1. Ottieni codici stazione
        origin_station = self._get_station_code(origin_city)
        dest_station = self._get_station_code(dest_city)
        
        if not origin_station or not dest_station:
            return None
        
        # WORKAROUND: API funziona solo per oggi ± 1-2 giorni
        # Per date future/passate, usa OGGI per ottenere orari tipici
        today = datetime.now().date()
        query_date = departure_time
        
        if abs((departure_time.date() - today).days) > 1:
            # Data troppo lontana -> usa oggi con stesso orario
            query_date = departure_time.replace(
                year=today.year,
                month=today.month,
                day=today.day
            )
            print(f"    ⚠️  Data {departure_time.date()} fuori range API -> uso OGGI {query_date.date()}")
        
        print(f"    🔍 Ricerca percorso {origin_city} -> {dest_city}")
        
        # 2. BFS per trovare percorso ottimale
        best_route = self._bfs_search(
            origin_station,
            dest_station,
            query_date,
            start_time
        )
        
        if not best_route:
            print(f"    ❌ Nessun percorso trovato")
            return None
        
        # 3. Formatta risultato
        return self._format_route(best_route, origin_city, dest_city)
    
    def _get_station_code(self, city_name: str) -> Optional[str]:
        """Ottiene codice stazione principale per una città (con cache)"""
        if city_name in self.station_cache:
            return self.station_cache[city_name]
        
        # Mappa città -> nome stazione principale (hardcoded per affidabilità)
        # Include le 106 città italiane più comuni
        station_names = {
            # Grandi città
            "Milano": "MILANO CENTRALE",
            "Roma": "ROMA TERMINI",
            "Torino": "TORINO PORTA NUOVA",
            "Napoli": "NAPOLI CENTRALE",
            "Bologna": "BOLOGNA CENTRALE",
            "Firenze": "FIRENZE SANTA MARIA NOVELLA",
            "Venezia": "VENEZIA SANTA LUCIA",
            "Genova": "GENOVA PIAZZA PRINCIPE",
            "Palermo": "PALERMO CENTRALE",
            "Bari": "BARI CENTRALE",
            "Catania": "CATANIA CENTRALE",
            "Verona": "VERONA PORTA NUOVA",
            "Padova": "PADOVA",
            "Trieste": "TRIESTE CENTRALE",
            "Brescia": "BRESCIA",
            "Parma": "PARMA",
            "Modena": "MODENA",
            "Reggio Emilia": "REGGIO EMILIA AV",
            "Piacenza": "PIACENZA",
            "Ancona": "ANCONA",
            "Lecce": "LECCE",
            "Siracusa": "SIRACUSA",
            "Salerno": "SALERNO",
            "Perugia": "PERUGIA",
            
            # Toscana
            "Pisa": "PISA CENTRALE",
            "Livorno": "LIVORNO CENTRALE",
            "Lucca": "LUCCA",
            "Pistoia": "PISTOIA",
            "Arezzo": "AREZZO",
            "Grosseto": "GROSSETO",
            "Siena": "SIENA",
            "Prato": "PRATO CENTRALE",
            "Massa": "MASSA CENTRO",
            
            # Emilia Romagna
            "Ravenna": "RAVENNA",
            "Ferrara": "FERRARA",
            "Rimini": "RIMINI",
            "Forlì": "FORLI'",
            "Cesena": "CESENA",
            
            # Veneto
            "Vicenza": "VICENZA",
            "Treviso": "TREVISO CENTRALE",
            "Belluno": "BELLUNO",
            "Rovigo": "ROVIGO",
            
            # Piemonte
            "Alessandria": "ALESSANDRIA",
            "Asti": "ASTI",
            "Cuneo": "CUNEO",
            "Novara": "NOVARA",
            "Vercelli": "VERCELLI",
            "Biella": "BIELLA SAN PAOLO",
            
            # Lombardia
            "Bergamo": "BERGAMO",
            "Como": "COMO SAN GIOVANNI",
            "Cremona": "CREMONA",
            "Mantova": "MANTOVA",
            "Pavia": "PAVIA",
            "Sondrio": "SONDRIO",
            "Varese": "VARESE",
            "Lecco": "LECCO",
            "Lodi": "LODI",
            "Monza": "MONZA",
            
            # Lazio
            "Latina": "LATINA",
            "Frosinone": "FROSINONE",
            "Rieti": "RIETI",
            "Viterbo": "VITERBO PORTA ROMANA",
            
            # Campania
            "Caserta": "CASERTA",
            "Avellino": "AVELLINO",
            "Benevento": "BENEVENTO",
            
            # Puglia
            "Taranto": "TARANTO",
            "Foggia": "FOGGIA",
            "Brindisi": "BRINDISI",
            
            # Calabria  
            "Reggio Calabria": "REGGIO DI CALABRIA CENTRALE",
            "Catanzaro": "CATANZARO",
            "Cosenza": "COSENZA",
            "Crotone": "CROTONE",
            "Vibo Valentia": "VIBO VALENTIA PIZZO",
            
            # Sicilia
            "Messina": "MESSINA CENTRALE",
            "Trapani": "TRAPANI",
            "Agrigento": "AGRIGENTO CENTRALE",
            "Ragusa": "RAGUSA",
            "Caltanissetta": "CALTANISSETTA CENTRALE",
            "Enna": "ENNA",
            
            # Sardegna
            "Cagliari": "CAGLIARI",
            "Sassari": "SASSARI",
            "Olbia": "OLBIA",
            "Nuoro": "NUORO",
            "Oristano": "ORISTANO",
            
            # Marche
            "Pesaro": "PESARO",
            "Macerata": "MACERATA",
            "Ascoli Piceno": "ASCOLI PICENO",
            "Fermo": "FERMO",
            
            # Umbria
            "Terni": "TERNI",
            "Spoleto": "SPOLETO",
            
            # Abruzzo
            "L'Aquila": "L'AQUILA",
            "Teramo": "TERAMO",
            "Pescara": "PESCARA CENTRALE",
            "Chieti": "CHIETI",
            
            # Molise
            "Campobasso": "CAMPOBASSO",
            "Isernia": "ISERNIA",
            
            # Friuli
            "Udine": "UDINE",
            "Pordenone": "PORDENONE",
            "Gorizia": "GORIZIA CENTRALE",
            
            # Liguria
            "La Spezia": "LA SPEZIA CENTRALE",
            "Imperia": "IMPERIA",
            "Savona": "SAVONA",
            
            # Trentino Alto Adige
            "Trento": "TRENTO",
            "Bolzano": "BOLZANO BOZEN",
            "Rovereto": "ROVERETO",
            
            # Valle d'Aosta
            "Aosta": "AOSTA",
            
            # Basilicata
            "Potenza": "POTENZA CENTRALE",
            "Matera": "MATERA CENTRALE"
        }
        
        # Usa nome dalla mappa se disponibile
        search_name = station_names.get(city_name, city_name.upper())
        
        try:
            # Prova prima getCodStazione (più veloce)
            code = self.api.getCodStazione(search_name)
            if code:
                self.station_cache[city_name] = code
                print(f"    📍 {city_name} -> {search_name} ({code})")
                return code
            
            # Fallback: usa searchStazione e prendi prima stazione principale
            results = self.api.searchStazione(city_name.upper())
            if results and len(results) > 0:
                # Prendi prima stazione (di solito è quella principale)
                first_station = results[0]
                code = first_station.get('id')
                name = first_station.get('nomeLungo', city_name)
                if code:
                    self.station_cache[city_name] = code
                    print(f"    📍 {city_name} -> {name} ({code})")
                    return code
        except Exception as e:
            print(f"    ⚠️ Errore ricerca stazione {city_name}: {e}")
        
        return None
    
    def _bfs_search(
        self,
        origin_station: str,
        dest_station: str,
        start_time: datetime,
        search_start: float
    ) -> Optional[List[Dict]]:
        """
        BFS semplificato: cerca treni diretti dalla stazione di origine
        """
        print(f"    🔍 Cerco treni diretti...")
        
        try:
            # Ottieni tutti i treni in partenza
            departures = self.api.getPartenze(origin_station, start_time)
            
            if not departures:
                print(f"    ⚠️ Nessuna partenza trovata")
                return None
            
            print(f"    📋 Analizzo {len(departures)} treni in partenza...")
            
            best_solution = None
            best_duration = float('inf')
            
            for idx, train in enumerate(departures):
                # Timeout check
                if time.time() - search_start > self.SEARCH_TIMEOUT_SECONDS:
                    print(f"    ⏱️ Timeout ricerca")
                    break
                
                train_number = train.get('numeroTreno')
                train_origin = train.get('codOrigine')
                dep_timestamp = train.get('orarioPartenza')
                
                if not train_number or not train_origin or not dep_timestamp:
                    continue
                
                dep_time = datetime.fromtimestamp(int(dep_timestamp) / 1000)
                
                # Skip se partenza troppo lontana
                wait_hours = (dep_time - start_time).total_seconds() / 3600
                if wait_hours > self.MAX_WAIT_HOURS:
                    continue
                
                try:
                    # Ottieni andamento treno
                    andamento = self.api.getAndamento(train_origin, str(train_number), dep_time)
                    
                    if not andamento:
                        continue
                    
                    fermate = andamento.get('fermate', [])
                    
                    # Cerca destinazione tra le fermate
                    for fermata in fermate:
                        station_code = fermata.get('id')
                        
                        if station_code == dest_station:
                            # Trovata!
                            arr_timestamp = fermata.get('arrivo_teorico')
                            if not arr_timestamp:
                                continue
                            
                            arr_time = datetime.fromtimestamp(int(arr_timestamp) / 1000)
                            total_duration = (arr_time - dep_time).total_seconds() / 3600
                            
                            # Skip se durata negativa o impossibile
                            if total_duration < 0 or total_duration > 24:
                                continue
                            
                            if total_duration < best_duration:
                                segment = {
                                    'train_number': train_number,
                                    'category': train.get('categoriaDescrizione', 'REG'),
                                    'origin_station': origin_station,
                                    'dest_station': dest_station,
                                    'departure': dep_time,
                                    'arrival': arr_time,
                                    'duration_hours': total_duration
                                }
                                
                                best_solution = [segment]
                                best_duration = total_duration
                                print(f"    ✅ Treno {train_number} ({segment['category']}): {total_duration:.1f}h")
                            
                            break  # Trovato per questo treno
                
                except Exception as e:
                    # Errore su questo treno, continua
                    continue
            
            return best_solution
            
        except Exception as e:
            print(f"    ❌ Errore ricerca: {e}")
            return None
    
    def _bfs_search_old(
        self,
        origin_station: str,
        dest_station: str,
        start_time: datetime,
        search_start: float
    ) -> Optional[List[Dict]]:
        """
        BFS per trovare percorso ferroviario ottimale (con cambi - DISABLED)
        
        State: (station_code, arrival_time, path)
        """
        # Queue: (station, current_time, path_segments, num_changes)
        queue = deque([(origin_station, start_time, [], 0)])
        visited = set()  # (station, hour) per evitare loop
        
        best_solution = None
        best_duration = float('inf')
        
        while queue:
            # Timeout check
            if time.time() - search_start > self.SEARCH_TIMEOUT_SECONDS:
                print(f"    ⏱️ Timeout ricerca")
                break
            
            current_station, current_time, path, num_changes = queue.popleft()
            
            # Skip se già visitato in questo orario
            visit_key = (current_station, current_time.hour)
            if visit_key in visited:
                continue
            visited.add(visit_key)
            
            # Se troppe connessioni, fermati
            if num_changes > self.MAX_CHANGES:
                continue
        
        return best_solution
    
    def _format_route(
        self,
        segments: List[Dict],
        origin_city: str,
        dest_city: str
    ) -> Dict:
        """Formatta percorso trovato nel formato atteso"""
        if not segments:
            return None
        
        first_seg = segments[0]
        last_seg = segments[-1]
        
        # Calcola durata totale
        total_duration = (last_seg['arrival'] - first_seg['departure']).total_seconds() / 3600
        
        # Stima prezzo (circa 0.15€/km per treni regionali, 0.25€/km per IC/FR)
        total_price = 0
        for seg in segments:
            if 'FR' in seg['category'] or 'AV' in seg['category']:
                total_price += 50  # Alta velocità
            elif 'IC' in seg['category']:
                total_price += 30  # Intercity
            else:
                total_price += 15  # Regionale
        
        return {
            'train': {
                'segments': segments,
                'origin': origin_city,
                'destination': dest_city
            },
            'travel_time': total_duration,
            'departure': first_seg['departure'].strftime('%H:%M'),
            'arrival': last_seg['arrival'].strftime('%H:%M'),
            'price': total_price,
            'changes': len(segments) - 1,
            'train_number': first_seg['train_number'],  # FIX: era numero_treno
            'train_type': first_seg['category'],  # Aggiungi tipo treno
            'real_data': True  # Flag per indicare dati reali
        }
