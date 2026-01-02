# 🚂 Italian Train Trip Planner

Sistema intelligente di pianificazione viaggi in treno per l'Italia, con integrazione API Trenitalia, OpenStreetMap e dati meteo.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)

## ✨ Caratteristiche

- **🗺️ Mappa Interattiva**: Selezione visuale delle città italiane con 65+ province
- **🧠 Smart Planning**: Suggerimenti AI basati su interessi, meteo e collegamenti ferroviari
- **🎯 Due Modalità**:
  - **Solo Partenza**: Il sistema suggerisce le destinazioni migliori
  - **Partenza + Arrivo**: Pianificazione percorso ottimale tra due città
- **🌤️ Integrazione Meteo**: Previsioni per ottimizzare le attività
- **🎨 POI Intelligenti**: Attrazioni basate su interessi (arte, storia, natura, cibo, ecc.)
- **🚆 API Trenitalia**: Orari e treni reali

## 🚀 Installazione e Avvio Rapido

### 1. Clone e Setup

```bash
git clone <repository-url>
cd SEProejct
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# oppure: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. **Avvio Backend** ⚠️ IMPORTANTE

```bash
python frontend/backend_server.py
```

**Output atteso:**
```
✅ Database loaded: 10 cities
🚂 Starting Italian Train Trip Planner Backend...
 * Running on http://127.0.0.1:5001
```

⚠️ **Lascia questo terminale aperto!**

### 3. Apertura Frontend

In un nuovo terminale (o doppio click):
```bash
open frontend/map_planner.html  # macOS
start frontend/map_planner.html  # Windows
```

## 🎮 Come Usare

### Modalità "Solo Partenza"
1. Clicca **"🧠 Solo Partenza"**
2. Clicca una città sulla mappa (diventa verde)
3. Imposta data e durata
4. Seleziona interessi (opzionale)
5. Clicca **"🔍 Pianifica Viaggio"**

### Modalità "Partenza + Arrivo"
1. Clicca **"🎯 Partenza + Arrivo"**
2. Clicca città di partenza (verde) e arrivo (rossa)
3. Imposta parametri e clicca pianifica

## 🔧 Troubleshooting

### ❌ Errore: "Failed to fetch" o "localhost not running"

**Causa**: Backend non in esecuzione

**Soluzione**:
1. Apri nuovo terminale
2. Attiva virtual environment:
   ```bash
   cd /path/to/SEProejct
   source .venv/bin/activate  # macOS/Linux
   ```
3. Avvia backend:
   ```bash
   python frontend/backend_server.py
   ```
4. Verifica output:
   ```
   * Running on http://127.0.0.1:5001
   ```
5. **NON chiudere il terminale**
6. Ricarica pagina browser (F5)

### Se la porta 5001 è occupata

```bash
# macOS/Linux
lsof -i :5001
kill -9 <PID>
python frontend/backend_server.py
```

### Se vedi errori di dipendenze

```bash
source .venv/bin/activate
pip install --upgrade flask flask-cors requests
python frontend/backend_server.py
```

## 📁 Struttura Progetto

```
SEProejct/
├── frontend/
│   ├── map_planner.html      # ⭐ Frontend con mappa
│   ├── backend_server.py     # 🔧 Backend Flask
│   ├── MODES_GUIDE.md        # 📖 Guida modalità
│   └── USER_GUIDE.md         # 📖 Guida utente
├── src/
│   ├── itinerary_planner.py  # Logica pianificazione
│   ├── city_database.py      # Database città + OSM
│   ├── travel_graph.py       # Algoritmo Dijkstra
│   ├── weather_provider.py   # API meteo
│   └── osm_provider.py       # OpenStreetMap
├── cache/                     # Cache OSM e grafo
├── examples/                  # Script demo
└── requirements.txt
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
