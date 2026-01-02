# Constraint-Based Train Trip Planner - Analisi API e Architettura

## 📊 Analisi Completa API Trenitalia (ViaggiaTreno)

### Endpoint Disponibili

#### 1. **Ricerca Stazioni** (`searchStazione`)
**Input:** Nome stazione (testo parziale)  
**Output:** Lista di stazioni con:
- `nomeLungo`: Nome completo della stazione
- `nomeBreve`: Nome abbreviato
- `label`: Etichetta città
- `id`: Codice stazione (es. S01700 per Milano Centrale)

**Utilità per il planner:** Permettere all'utente di cercare e selezionare stazioni di partenza/arrivo.

---

#### 2. **Elenco Stazioni per Regione** (`getStazioniByRegione`)
**Input:** Codice regione (1=Lombardia, ecc.)  
**Output:** Lista completa con:
- Coordinate geografiche (`lat`, `lon`)
- Nome stazione
- Tipo stazione
- Codice identificativo

**Utilità per il planner:** Creare database locale di stazioni con coordinate per integrazione OSM.

---

#### 3. **Partenze da Stazione** (`getPartenze`)
**Input:** Codice stazione + orario  
**Output:** Array di treni in partenza con **65+ campi**, tra cui:
- `numeroTreno`: Identificativo treno
- `categoria`: REG, FR, IC, ecc.
- `destinazione`: Stazione di arrivo
- `orarioPartenza`: Timestamp partenza programmata
- `ritardo`: Ritardo in minuti (int)
- `binarioEffettivoPartenzaDescrizione`: Binario effettivo
- `binarioProgrammatoPartenzaDescrizione`: Binario programmato
- `circolante`: Boolean, indica se il treno è in circolazione
- `provvedimento`: Codice provvedimento (cancellazioni, ritardi, ecc.)
- `compTipologiaTreno`: Tipologia (regionale, intercity, frecciarossa, ecc.)
- `ultimoRilev`: Timestamp ultimo rilevamento

**Utilità per il planner:** 
- Filtrare treni per categoria
- Escludere treni con ritardi eccessivi
- Verificare disponibilità in tempo reale

---

#### 4. **Arrivi a Stazione** (`getArrivi`)
**Input:** Codice stazione + orario  
**Output:** Simile a Partenze, ma con focus su:
- `origine`: Stazione di partenza
- `orarioArrivo`: Timestamp arrivo programmato
- `binarioEffettivoArrivoDescrizione`: Binario effettivo

**Utilità per il planner:** Sincronizzare coincidenze e verificare arrivi.

---

#### 5. **Soluzioni di Viaggio** (`getIndicazioniViaggio`)
**Input:** Codice stazione origine + destinazione + orario  
**Output:** Array di soluzioni complete con:
- `orarioPartenza`: Orario di partenza
- `orarioArrivo`: Orario di arrivo
- `durata`: Durata totale del viaggio (stringa formato HH:MM)
- `cambi`: Numero di cambi necessari
- `soluzione`: Dettagli completi delle tratte
  - Per ogni tratta: treno, orari, stazioni intermedie

**Note:** Durante il test, non ha restituito risultati (possibile problema di formato orario o API non sempre affidabile per questa funzione).

**Utilità per il planner:** **Funzione principale** per ottenere percorsi completi. Se non disponibile, dovremo implementare un algoritmo di ricerca percorsi manuale.

---

#### 6. **Andamento Treno in Tempo Reale** (`getAndamento`)
**Input:** Codice stazione origine + numero treno + timestamp partenza  
**Output:** **Oggetto dettagliatissimo** con:
- `tipoTreno`: Tipologia
- `ritardo`: Ritardo complessivo
- `fermate`: Array di **tutte le fermate** con:
  - `stazione`: Nome stazione
  - `id`: Codice stazione
  - `arrivo_teorico` / `partenza_teorica`: Orari programmati (timestamp)
  - `arrivoReale` / `partenzaReale`: Orari effettivi (timestamp)
  - `ritardoArrivo` / `ritardoPartenza`: Ritardi specifici per fermata
  - `binarioEffettivoPartenzaDescrizione`: Binario
  - `tipoFermata`: P (Partenza), F (Fermata), A (Arrivo)
  - `listaCorrispondenze`: Treni in coincidenza
- `provvedimenti`: Lista di provvedimenti straordinari
- `anormalita`: Lista di anomalie
- `segnalazioni`: Lista di segnalazioni
- `oraUltimoRilevamento`: Ultimo aggiornamento posizione
- `stazioneUltimoRilevamento`: Stazione attuale

**Utilità per il planner:** 
- Tracciare posizione treno in tempo reale
- Prevedere ritardi su tutta la tratta
- Valutare affidabilità delle coincidenze
- Mostrare informazioni dettagliate all'utente

---

#### 7. **Informazioni Mobilità** (`getInfoMob`)
**Input:** Nessuno  
**Output:** HTML/XML con avvisi di servizio sulla rete

**Note:** Restituisce stringhe HTML, non JSON. Contiene info come:
- "Circolazione regolare sulla rete AV"
- "Linea X-Y: circolazione sospesa per..."
- Avvisi di scioperi, lavori, ecc.

**Utilità per il planner:** Mostrare avvisi generali all'utente, eventualmente parsare HTML per estrarre info strutturate.

---

## 🎯 Constraint Implementabili

Basandoci sui dati disponibili dall'API, ecco i constraint che possiamo implementare:

### Constraint Temporali
1. **Orario preferito di partenza** (`departure_time`)
   - Exact: Partenza esatta
   - Before: Partenza prima di un orario
   - After: Partenza dopo un orario
   - Range: Finestra temporale

2. **Orario preferito di arrivo** (`arrival_time`)
   - Before: Arrivo prima di un orario
   - After: Arrivo dopo un orario

3. **Durata massima** (`max_duration`)
   - Tempo massimo di viaggio accettabile

4. **Tempo minimo di coincidenza** (`min_transfer_time`)
   - Tempo buffer tra treni per cambi (default: 5-10 minuti)

### Constraint sui Treni
5. **Categoria treno** (`train_categories`)
   - Include: Solo FR, IC, REG, ecc.
   - Exclude: Escludere categorie specifiche
   - Esempio: Solo alta velocità (FR), no regionali

6. **Numero massimo di cambi** (`max_transfers`)
   - 0: Solo treni diretti
   - 1, 2, 3+: Numero massimo di coincidenze

7. **Ritardo massimo accettabile** (`max_delay`)
   - Escludere treni con ritardo superiore a N minuti
   - Valutazione real-time dell'affidabilità

### Constraint Geografici (con integrazione OSM)
8. **Distanza massima da punto** (`max_distance_from_point`)
   - Filtrare stazioni entro X km da una posizione
   - Esempio: "Stazioni entro 5km dal centro di Milano"

9. **Preferenza stazioni centrali** (`prefer_central_stations`)
   - Priorità a stazioni principali vs. periferiche

### Constraint Meteo (con integrazione OpenWeather)
10. **Condizioni meteo minime** (`weather_constraints`)
    - Evitare viaggi con previsione di neve/tempeste
    - Preferire orari con meteo favorevole

11. **Temperatura preferita** (`temperature_range`)
    - Evitare viaggi con temperature estreme

### Constraint di Servizio
12. **Provvedimenti** (`avoid_disruptions`)
    - Escludere treni con provvedimenti attivi
    - Escludere treni cancellati o con problemi

13. **Circolazione verificata** (`only_confirmed_trains`)
    - Solo treni confermati come circolanti

---

## 🔗 Architettura di Integrazione

### 1. Sistema Multi-API

```
┌─────────────────────────────────────────────────────────┐
│          Constraint-Based Train Trip Planner            │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌────────▼────────┐
│   Trenitalia   │  │ OpenStreetMap│  │  OpenWeather    │
│      API       │  │  (Nominatim)  │  │      API        │
└────────────────┘  └───────────────┘  └─────────────────┘
        │                   │                   │
        ├─ Treni            ├─ Coordinate       ├─ Meteo
        ├─ Stazioni         ├─ Distanze         ├─ Previsioni
        ├─ Orari            ├─ POI              └─ Alert
        └─ Ritardi          └─ Routing
```

### 2. OpenStreetMap (Nominatim) - Integrazione

**Funzionalità da implementare:**

1. **Geocoding Stazioni**
   ```python
   def enrich_station_with_coordinates(station_code):
       # API Trenitalia → coordinate
       # Salvare in database locale per caching
       return {
           'code': station_code,
           'lat': 45.486,
           'lon': 9.204,
           'address': 'Milano Centrale, Milano, Italia'
       }
   ```

2. **Calcolo Distanze**
   ```python
   def find_stations_near_point(lat, lon, max_distance_km):
       # Filtrare stazioni entro raggio
       # Usare formula Haversine o OSM API
       return filtered_stations
   ```

3. **Servizi nelle Vicinanze**
   ```python
   def find_amenities_near_station(station_code, amenity_type):
       # amenity_type: hotel, restaurant, parking, taxi
       # Restituire POI OSM
       return nearby_amenities
   ```

**API Nominatim:**
- Endpoint: `https://nominatim.openstreetmap.org/`
- Rate limit: 1 req/sec per uso gratuito
- Nessuna API key richiesta (con User-Agent appropriato)

### 3. OpenWeather API - Integrazione

**Funzionalità da implementare:**

1. **Meteo Attuale**
   ```python
   def get_current_weather(lat, lon):
       # OpenWeather Current Weather API
       return {
           'temp': 15.2,
           'condition': 'Clear',
           'humidity': 65,
           'wind_speed': 3.5
       }
   ```

2. **Previsioni**
   ```python
   def get_weather_forecast(lat, lon, departure_time):
       # OpenWeather Forecast API (5 giorni, 3h step)
       # Interpolare per orario specifico
       return weather_at_departure
   ```

3. **Alert Meteo**
   ```python
   def get_weather_alerts(lat, lon):
       # OpenWeather Alerts API
       # Alert per tempeste, neve, ecc.
       return alerts
   ```

**API OpenWeather:**
- Endpoint: `https://api.openweathermap.org/data/2.5/`
- API Key: Richiesta (gratuita fino a 60 calls/min)
- Costo: Free tier disponibile

---

## 🧠 Algoritmo di Pianificazione

### Approccio: Constraint Satisfaction Problem (CSP)

1. **Variabili:**
   - Treni selezionati per ogni tratta
   - Orari di partenza/arrivo
   - Stazioni di cambio

2. **Domini:**
   - Treni disponibili per ogni tratta
   - Orari possibili

3. **Constraint:**
   - Tutti i constraint definiti sopra
   - Vincoli di precedenza temporale
   - Compatibilità coincidenze

4. **Algoritmo:**
   ```
   1. Raccogliere tutte le soluzioni possibili (da API o calcolo manuale)
   2. Filtrare per constraint "hard" (es. orario, categoria treno)
   3. Ordinare per constraint "soft" (es. durata, cambi)
   4. Applicare pesi per preferenze utente
   5. Restituire top-N soluzioni
   ```

### Esempio di Implementazione

```python
class TripConstraint:
    def evaluate(self, trip_solution):
        """Restituisce True se il constraint è soddisfatto"""
        pass
    
    def weight(self):
        """Peso del constraint (soft constraints)"""
        return 1.0

class MaxDelayConstraint(TripConstraint):
    def __init__(self, max_delay_minutes):
        self.max_delay = max_delay_minutes
    
    def evaluate(self, trip_solution):
        return all(train.delay <= self.max_delay for train in trip_solution.trains)

class TripPlanner:
    def __init__(self):
        self.constraints = []
        self.api = apitr()
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)
    
    def find_solutions(self, origin, destination, departure_time):
        # 1. Ottenere soluzioni base dall'API
        raw_solutions = self.api.getIndicazioniViaggio(origin, destination, departure_time)
        
        # 2. Se API non funziona, calcolare manualmente
        if not raw_solutions:
            raw_solutions = self._compute_solutions_manually(origin, destination, departure_time)
        
        # 3. Filtrare per constraint hard
        valid_solutions = [s for s in raw_solutions if self._satisfies_constraints(s)]
        
        # 4. Ordinare per score
        scored_solutions = [(s, self._score_solution(s)) for s in valid_solutions]
        scored_solutions.sort(key=lambda x: x[1], reverse=True)
        
        # 5. Restituire top-N
        return [s for s, score in scored_solutions[:10]]
    
    def _satisfies_constraints(self, solution):
        return all(c.evaluate(solution) for c in self.constraints)
    
    def _score_solution(self, solution):
        return sum(c.weight() * c.evaluate(solution) for c in self.constraints)
```

---

## 📋 Prossimi Passi per Implementazione

### Fase 1: Core System (1-2 settimane)
- [x] Analisi API Trenitalia
- [ ] Creare modelli dati (Station, Train, Trip, Solution)
- [ ] Implementare wrapper API Trenitalia più robusto
- [ ] Implementare cache per ridurre chiamate API
- [ ] Sistema di gestione constraint base

### Fase 2: Algoritmo di Pianificazione (2-3 settimane)
- [ ] Implementare ricerca percorsi (se API soluzioni non funziona)
- [ ] Algoritmo CSP per filtraggio constraint
- [ ] Sistema di scoring e ranking soluzioni
- [ ] Gestione coincidenze e tempi di cambio

### Fase 3: Integrazione API Esterne (1-2 settimane)
- [ ] Integrazione OpenStreetMap/Nominatim
- [ ] Cache coordinate stazioni
- [ ] Calcolo distanze geografiche
- [ ] Integrazione OpenWeather
- [ ] Previsioni meteo per orari viaggio

### Fase 4: UI e Testing (2-3 settimane)
- [ ] CLI/GUI per input constraint
- [ ] Visualizzazione risultati
- [ ] Testing con casi reali
- [ ] Ottimizzazione performance
- [ ] Documentazione

---

## 🚀 Tecnologie Consigliate

### Backend
- **Python 3.8+**: Linguaggio principale
- **requests**: HTTP client per API
- **SQLite/PostgreSQL**: Database per cache stazioni
- **FastAPI/Flask**: API REST se serve interfaccia web
- **python-constraint**: Libreria CSP (opzionale)

### Data Processing
- **pandas**: Analisi e manipolazione dati treni
- **geopy**: Calcoli geografici (distanze, coordinate)
- **datetime/dateutil**: Gestione orari e timestamp

### Caching
- **redis**: Cache in-memory per dati real-time
- **diskcache**: Cache su disco per coordinate stazioni

### Testing
- **pytest**: Framework testing
- **unittest.mock**: Mock API calls
- **faker**: Generazione dati test

---

## 💡 Considerazioni Finali

### Punti di Forza
1. ✅ API Trenitalia molto completa (65+ campi per treno)
2. ✅ Dati real-time su ritardi e posizione treni
3. ✅ Coordinate geografiche disponibili
4. ✅ Integrazione con OSM e OpenWeather fattibile

### Potenziali Problemi
1. ⚠️ API soluzioni viaggio potrebbe non essere affidabile
2. ⚠️ Necessario implementare algoritmo di routing manuale
3. ⚠️ Rate limiting possibile (non documentato)
4. ⚠️ Cache essenziale per performance

### Raccomandazioni
1. **Iniziare con MVP**: Solo constraint base (orario, cambi, categoria)
2. **Testare API estensivamente**: Verificare quali endpoint sono affidabili
3. **Implementare cache aggressiva**: Ridurre dipendenza da API
4. **Backup plan**: Se API soluzioni non funziona, implementare ricerca grafo
5. **User feedback**: Sistema di rating soluzioni per migliorare algoritmo

---

## 📚 Risorse Utili

- **API Trenitalia (non ufficiale)**: Già integrata nel progetto
- **Nominatim API**: https://nominatim.org/release-docs/develop/api/Overview/
- **OpenWeather API**: https://openweathermap.org/api
- **python-constraint**: https://github.com/python-constraint/python-constraint
- **Algoritmi CSP**: Russell & Norvig, "Artificial Intelligence: A Modern Approach"

---

**Documento creato il**: 2 Gennaio 2026  
**Autore**: GitHub Copilot  
**Progetto**: Constraint-Based Train Trip Planner - Software Engineering Project
