# 🚂 Italian Train Trip Planner

Sistema intelligente di pianificazione viaggi in treno per l'Italia, con integrazione API Trenitalia, OpenStreetMap e dati meteo.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Cities](https://img.shields.io/badge/cities-106-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Caratteristiche

- **🗺️ Mappa Interattiva**: Selezione visuale di **106 province italiane** caricate dinamicamente da OpenStreetMap
- **🧠 Smart Planning AI**: Suggerimenti intelligenti basati su interessi, meteo e collegamenti ferroviari
- **🎯 Due Modalità**:
  - **Solo Partenza**: Il sistema suggerisce automaticamente le destinazioni migliori
  - **Partenza + Arrivo**: Pianificazione percorso ottimale tra due città specifiche
- **📍 Itinerari Dettagliati**: Visualizzazione completa giorno per giorno con POI, costi e tempistiche
- **🌤️ Integrazione Meteo**: Previsioni a 5 giorni per ottimizzare le attività
- **🎨 POI Intelligenti**: Oltre 3000 attrazioni da OpenStreetMap categorizzate per interessi
- **🚆 API Trenitalia**: Orari e collegamenti ferroviari reali
- **💰 Stima Costi**: Calcolo automatico budget giornaliero e totale

## 🏗️ Architettura

```
SEProejct/
├── frontend/
│   ├── backend_server.py      # Flask API server
│   └── map_planner.html       # Single-page web interface
├── src/
│   ├── itinerary_planner.py   # Core planning logic
│   ├── city_database.py       # 106 cities database manager
│   ├── travel_graph.py        # Dijkstra routing algorithm
│   ├── osm_provider.py        # OpenStreetMap integration
│   └── weather_provider.py    # Weather API integration
├── data/
│   ├── cities_database.json   # 106 Italian provinces with POIs
│   └── provinces_static.json  # Fallback database
└── scripts/
    └── build_complete_database.py  # OSM data downloader
```

## 🚀 Installazione e Avvio

### 1. Clone e Setup

```bash
git clone https://github.com/TommasoAiello08/SE_Proj-Train_Trip_Planner.git
cd SEProejct
python3 -m venv .venv
pip install -r requirements.txt
```

### 2. Avvio Sistema (Automatico) ⚡

```bash
source .venv/bin/activate  # macOS/Linux
# oppure: .venv\Scripts\activate  # Windows
./start.sh
```

Lo script `start.sh` automaticamente:
- 🔄 Termina processi precedenti sulle porte 5001 e 8080
- 🚀 Avvia il backend Flask (porta 5001)
- 🌐 Avvia il frontend HTTP server (porta 8080)
- 🔗 Apre automaticamente il browser su **http://localhost:8080/map_planner.html**
- 📝 Log disponibili in `/tmp/backend.log` e `/tmp/frontend.log`

**Per fermare i server:**
```bash
./stop.sh
```

### 3. Avvio Manuale (Opzionale)

Se preferisci avviare manualmente (2 terminali):

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
python frontend/backend_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python3 -m http.server 8080
```

Apri nel browser: **http://localhost:8080/map_planner.html**

## 🎮 Come Usare

### Modalità "Solo Partenza" 🧠
1. Clicca **"🧠 Solo Partenza"** (modalità predefinita)
2. Clicca una città sulla mappa (diventa **verde**)
3. Seleziona data di partenza e durata (1-5 giorni)
4. Scegli interessi (opzionale): arte, storia, natura, cibo, mare, montagna
5. Clicca **"🔍 Pianifica Viaggio"**
6. Visualizza l'itinerario dettagliato sotto la mappa

### Modalità "Partenza + Arrivo" 🎯
1. Clicca **"🎯 Partenza + Arrivo"**
2. Clicca città di partenza (**verde**) poi città di arrivo (**rossa**)
3. Imposta parametri e clicca **"🔍 Pianifica Viaggio"**
4. Il sistema pianifica il percorso ottimale tra le due città

### Risultato Itinerario

L'itinerario mostra per ogni giorno:
- 🏙️ **Città e data**
- 🚂 **Viaggio in treno** (durata e orari stimati)
- 🎯 **Attività del giorno** con:
  - Nome e tipo attrazione
  - ⏱️ Durata visita
  - 💰 Costo ingresso
  - ⭐ Rating qualità
- 📊 **Riepilogo giornaliero**: ore disponibili e costo totale

## 🔧 Troubleshooting

### ❌ Errore: "Failed to fetch" o CORS errors

**Soluzione Rapida:**
```bash
./stop.sh && ./start.sh
```

**Causa**: Frontend non servito via HTTP o backend spento

**Soluzione Manuale**:
1. Verifica che **entrambi i server** siano attivi:
   - **Backend**: porta 5001
   - **Frontend**: porta 8080
2. Accedi a: **http://localhost:8080/map_planner.html** (non file://)
3. Controlla i log: `/tmp/backend.log` e `/tmp/frontend.log`
4. Ricarica pagina browser (F5)

**⚠️ Importante**: NON aprire il file HTML direttamente con doppio click. Usa sempre `./start.sh` per avviare il sistema.

### Se la porta 5001 o 8080 è occupata

```bash
./stop.sh  # Termina automaticamente processi sulle porte 5001 e 8080
./start.sh # Riavvia il sistema
```

**Verifica manuale:**
```bash
lsof -i :5001  # Backend
lsof -i :8080  # Frontend
```

### Mappa non carica le 106 città

1. Verifica backend logs: deve mostrare `✅ Database loaded: 106 cities`
2. Controlla browser console (F12) per errori API
3. Test manuale endpoint: `curl http://localhost:5001/api/cities`
4. Se vedi meno di 106 città, rigenera database:
   ```bash
   python scripts/build_complete_database.py
   ```

### Errori di dipendenze

```bash
source .venv/bin/activate
pip install --upgrade flask flask-cors requests
```

## 📁 Struttura Progetto

```
SEProejct/
├── frontend/
│   ├── backend_server.py       # Flask API (porta 5001)
│   ├── map_planner.html        # Single-page interface
│   ├── MODES_GUIDE.md          # Guida modalità
│   └── USER_GUIDE.md           # Guida utente
├── src/
│   ├── itinerary_planner.py    # Core planning logic
│   ├── city_database.py        # Database manager (106 cities)
│   ├── travel_graph.py         # Dijkstra routing
│   ├── weather_provider.py     # Weather API
│   ├── osm_provider.py         # OpenStreetMap integration
│   └── trenitalia_provider.py  # Trenitalia API
├── data/
│   ├── cities_database.json    # 106 provinces + 3000+ POIs
│   ├── provinces_static.json   # Fallback database (20 cities)
│   └── cache/                  # OSM/Weather response cache
├── scripts/
│   └── build_complete_database.py  # OSM downloader (107 provinces)
└── docs/
    ├── README.md               # Questo file
    ├── ANALISI_API_E_ARCHITETTURA.md
    ├── RIEPILOGO_PROGETTO.md
    └── SINTESI_ANALISI.md
```

## 🛠️ Scripts Utili

### Avvio/Arresto Sistema
```bash
source .venv/bin/activate
./start.sh  # Avvia backend + frontend + apre browser
./stop.sh   # Ferma tutti i server
```

### Rigenera Database da OSM
```bash
python scripts/build_complete_database.py
# Download 107 province italiane con ~30 POI ciascuna
# Tempo: ~5-6 minuti con retry automatico
```

### Verifica Salute Sistema
```bash
curl http://localhost:5001/api/health
# Output: {"message":"OK","status":"healthy"}

curl http://localhost:5001/api/cities | python -m json.tool | head -20
# Verifica città caricate
```

## 👥 Contributors

- **Alessandro**: Bug fixes e validazioni (branch fix/ale)
- **Tommaso**: Database expansion e frontend enhancement

## 📄 License

MIT License - vedi LICENSE file per dettagli

---

**🚀 Quick Start**: 
```bash
source .venv/bin/activate && ./start.sh
```

## 🎯 API Backend

### POST `/api/plan`

```json
{
  "mode": "smart_open",
  "start_city": "Milano",
  "end_city": "Napoli",
  "start_date": "2026-01-10",
  "duration": 3,
  "interests": ["arte", "storia"]
}
```

## 📊 Algoritmi

- **Dijkstra**: Percorso ottimale tra città
- **Knapsack**: Selezione POI giornalieri
- **Greedy**: Scoring attrazioni
- **Haversine**: Calcolo distanze

## 🔑 API Utilizzate

- **Trenitalia ViaggiaTreno**: Orari treni (pubblica)
- **OpenStreetMap**: Geocoding e POI
- **OpenWeatherMap**: Previsioni meteo

## 📝 License

MIT License

---

**Buon viaggio! 🚂🇮🇹**
