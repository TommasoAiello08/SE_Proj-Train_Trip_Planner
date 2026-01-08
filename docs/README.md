# 🚂 Italian Train Trip Planner - Documentation

Advanced train travel planning system using **Dynamic Programming optimization**, real-time Trenitalia data, OpenStreetMap POI curation, and weather integration.

## 📋 Documentation Index

- [🏠 Main README](../README.md) - Quick start and overview
- [🧮 DP Algorithm](DP_ALGORITHM.md) - **NEW**: Complete Dynamic Programming explanation
- [📊 Optimization Report](OPTIMIZATION_REPORT.md) - Performance analysis and improvements
- [📝 Project Summary](RIEPILOGO_PROGETTO.md) - Italian project overview
- [🔍 API Analysis](ANALISI_API_E_ARCHITETTURA.md) - API architecture and design
- [📈 Analysis Summary](SINTESI_ANALISI.md) - Condensed technical analysis

## ✨ Key Features (v2.0)

- **🧮 Dynamic Programming Route Optimizer**: Multi-day trips with intelligent city selection
- **🎯 MAX 2 Days Per City**: Enforced constraint for diverse itineraries  
- **🗺️ 106 Italian Cities**: Complete coverage with train connections
- **📍 Curated POIs**: 20 attractions per city from 28+ OpenStreetMap categories
- **🚆 Real Train Integration**: Trenitalia API with time-aware scheduling
- **⏰ Running Clock System**: Realistic 8:00-21:00 daily schedule
- **🌤️ Weather-Aware**: 5-day forecasts for activity optimization
- **💰 Smart Cost Estimation**: Detailed budget breakdown per day

## 🛠 Technologies

- **Python 3.10+**: Core language
- **Dynamic Programming**: Multi-day route optimization with constraints
- **Trenitalia ViaggiaTreno API**: Real-time train data
- **OpenStreetMap Overpass**: POI data (tourism, historic, leisure, natural, amenity)
- **OpenWeather API**: Weather forecasts
- **Flask**: REST API backend (port 5001)
- **Leaflet.js**: Interactive map with route visualization
- **JSON Cache**: OSM POI caching system

## 📦 Installazione

### Prerequisiti

- Python 3.8 o superiore
- pip (package manager Python)
- Virtual environment (consigliato)

### Setup

1. **Clone il repository** (o scarica i file):
   ```bash
   cd SEProejct
   ```

2. **Crea e attiva virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Su macOS/Linux
   # oppure
   .venv\Scripts\activate     # Su Windows
   ```

3. **Installa dipendenze**:
   ```bash
   pip install requests
   # Altre dipendenze verranno aggiunte durante lo sviluppo
   ```

4. **Testa l'installazione**:
   ```bash
   python api_explorer.py
   ```

## 🚀 Utilizzo

### 1. Esplorare l'API Trenitalia

Per capire quali dati sono disponibili:

```bash
python api_explorer.py
```

Questo script mostra:
- Tutte le stazioni disponibili
- Treni in partenza/arrivo
- Dettagli completi su ogni treno
- Statistiche sui ritardi

### 2. Demo del Planner con Constraint

Esegui la demo con scenari predefiniti:

```bash
python demo_planner.py
```

Scenari disponibili:
- **Scenario 1**: Viaggio di lavoro (solo alta velocità, ritardo max 5 min)
- **Scenario 2**: Viaggio economico (tutte le categorie, priorità velocità)
- **Scenario 3**: Analisi ritardi in tempo reale

### 3. Integrazione Meteo

Demo di integrazione con OpenWeather:

```bash
python openweather_integration.py
```

**Nota**: Per usare dati meteo reali, registrati gratuitamente su [openweathermap.org](https://openweathermap.org/api) e inserisci la tua API key nel file.

### 4. Uso Programmatico

```python
from datetime import datetime
from demo_planner import SimpleTripPlanner, MaxDelayConstraint, TrainCategoryConstraint

# Crea planner
planner = SimpleTripPlanner()

# Aggiungi constraint
planner.add_constraint(
    MaxDelayConstraint(max_delay_minutes=10, is_hard=True)
)

planner.add_constraint(
    TrainCategoryConstraint(allowed_categories=['FR', 'FA'], is_hard=True)
)

# Cerca soluzioni
trains = planner.find_departures("MILANO CENTRALE", datetime.now())
filtered = planner.filter_by_constraints(trains)
planner.display_results(filtered, max_results=5)
```

## 🎯 Constraint Supportati

### Constraint Temporali

| Constraint | Tipo | Descrizione |
|------------|------|-------------|
| `DepartureTimeConstraint` | Hard | Finestra temporale per la partenza |
| `ArrivalTimeConstraint` | Hard | Orario massimo/minimo di arrivo |
| `MaxDurationConstraint` | Hard | Durata massima del viaggio |
| `MinTransferTimeConstraint` | Hard | Tempo minimo tra coincidenze |

### Constraint sui Treni

| Constraint | Tipo | Descrizione |
|------------|------|-------------|
| `TrainCategoryConstraint` | Hard/Soft | Categorie ammesse (FR, IC, REG, ecc.) |
| `MaxTransfersConstraint` | Hard | Numero massimo di cambi |
| `MaxDelayConstraint` | Hard | Ritardo massimo accettabile |
| `PreferFastTrainsConstraint` | Soft | Preferenza per treni veloci |

### Constraint Geografici (via OSM)

| Constraint | Tipo | Descrizione |
|------------|------|-------------|
| `MaxDistanceFromPointConstraint` | Hard | Stazioni entro X km da un punto |
| `PreferCentralStationsConstraint` | Soft | Preferenza per stazioni centrali |

### Constraint Meteo (via OpenWeather)

| Constraint | Tipo | Descrizione |
|------------|------|-------------|
| `AvoidBadWeatherConstraint` | Hard | Evita maltempo (tempeste, neve) |
| `TemperatureRangeConstraint` | Soft | Temperatura confortevole |
| `PreferGoodWeatherConstraint` | Soft | Preferenza per bel tempo |

## 🏗️ Architettura

```
┌─────────────────────────────────────────┐
│         User Interface (CLI)            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Trip Planner Core                 │
│  ┌────────────────────────────────┐     │
│  │  Constraint Manager            │     │
│  │  - Parse & validate            │     │
│  └────────────────────────────────┘     │
│  ┌────────────────────────────────┐     │
│  │  Route Finder                  │     │
│  │  - Graph search                │     │
│  └────────────────────────────────┘     │
│  ┌────────────────────────────────┐     │
│  │  Solution Scorer               │     │
│  │  - Rank & sort                 │     │
│  └────────────────────────────────┘     │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼───┐  ┌───▼────┐
│Trenit.│  │ OSM  │  │Weather │
│  API  │  │  API │  │  API   │
└───────┘  └──────┘  └────────┘
```

### Componenti Principali

1. **Constraint Manager**: Gestisce e valida tutti i constraint
2. **Route Finder**: Trova percorsi tra stazioni (algoritmi grafo)
3. **Solution Scorer**: Calcola punteggi e ordina soluzioni
4. **API Integrator**: Wrapper per API esterne con cache

## 📁 File del Progetto

```
SEProejct/
├── apitr.py                          # Libreria API Trenitalia
├── api_explorer.py                   # Tool esplorazione API (✅ completo)
├── demo_planner.py                   # Demo planner con constraint (✅ completo)
├── openweather_integration.py        # Integrazione meteo (✅ completo)
├── ANALISI_API_E_ARCHITETTURA.md    # Documentazione tecnica (✅ completo)
├── RIEPILOGO_PROGETTO.md            # Sintesi e roadmap (✅ completo)
├── README.md                         # Questo file
├── main.py                           # Test base API
└── .venv/                            # Virtual environment
```

### Documentazione

- **[ANALISI_API_E_ARCHITETTURA.md](./ANALISI_API_E_ARCHITETTURA.md)**: Analisi completa dell'API Trenitalia, dettagli endpoint, architettura sistema
- **[RIEPILOGO_PROGETTO.md](./RIEPILOGO_PROGETTO.md)**: Sintesi esecutiva, constraint implementabili, roadmap, best practices

## 📊 Esempio Output

```
================================================================================
📊 RISULTATI - Top 3 treni
================================================================================

1. Treno FR 9615
   Destinazione: ROMA TERMINI
   Partenza: 10:00
   ✅ In orario
   Binario: 19
   Tipologia: Frecciarossa
   🌤️  Meteo partenza: Cielo sereno, 20°C

2. Treno IC 605
   Destinazione: ROMA TERMINI
   Partenza: 10:30
   ⚠️  Ritardo: 3 minuti
   Binario: 12
   Tipologia: Intercity
   🌤️  Meteo partenza: Parzialmente nuvoloso, 18°C

3. Treno FR 9620
   Destinazione: ROMA TERMINI
   Partenza: 11:00
   ✅ In orario
   Binario: 20
   Tipologia: Frecciarossa
   🌤️  Meteo partenza: Cielo sereno, 21°C
```

## 🗓️ Roadmap

### ✅ Fase 1: Analisi e Prototipo (Completata)
- [x] Analisi API Trenitalia
- [x] Script esplorativo completo
- [x] Demo con constraint base
- [x] Documentazione tecnica

### 🔨 Fase 2: Core Implementation (In corso)
- [ ] Modelli dati (Station, Train, Trip, Solution)
- [ ] Wrapper API robusto con retry/cache
- [ ] Database SQLite per stazioni
- [ ] Sistema constraint completo
- [ ] Algoritmo ricerca percorsi (grafo)

### 📅 Fase 3: Integrazioni API (Pianificata)
- [ ] Client OSM Nominatim completo
- [ ] Client OpenWeather completo
- [ ] Cache intelligente
- [ ] Constraint geografici e meteo

### 🎨 Fase 4: UI e Deploy (Pianificata)
- [ ] Web UI (FastAPI + Vue/React)
- [ ] API REST
- [ ] Docker container
- [ ] Deploy cloud

## 🤝 Contribuire

Questo è un progetto accademico per il corso di Software Engineering. Contributi e suggerimenti sono benvenuti!

### Come Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

### Aree di Contributo

- 🐛 Bug fixes
- ✨ Nuove feature/constraint
- 📝 Documentazione
- 🧪 Test automatizzati
- 🎨 UI/UX improvements

## 📄 Licenza

Questo progetto è sviluppato per scopi educativi nell'ambito del corso di Software Engineering.

## 👥 Autori

- **Tommaso Aiello** - Studente Magistrale, Software Engineering

## 🙏 Ringraziamenti

- **API Trenitalia (ViaggiaTreno)**: Per i dati real-time sui treni
- **OpenStreetMap**: Per i dati geografici
- **OpenWeather**: Per le previsioni meteo
- **GitHub Copilot**: Per l'assistenza nello sviluppo

## 📞 Supporto

Per domande o problemi:
- Apri una Issue su GitHub
- Consulta la documentazione in [ANALISI_API_E_ARCHITETTURA.md](./ANALISI_API_E_ARCHITETTURA.md)

---

**Ultima modifica**: 2 Gennaio 2026  
**Stato**: 🟢 In sviluppo attivo  
**Versione**: 0.1.0 (Prototipo)
