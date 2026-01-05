# 🚂 Italian Train Trip Planner

Intelligent train travel planning system for Italy, with Trenitalia API integration, OpenStreetMap, and weather data.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Cities](https://img.shields.io/badge/cities-106-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **🗺️ Interactive Map**: Visual selection of **106 Italian provinces** dynamically loaded from OpenStreetMap
- **🧠 Smart AI Planning**: Intelligent suggestions based on interests, weather, and train connections
- **🎯 Two Modes**:
  - **Departure Only**: System automatically suggests the best destinations
  - **Departure + Arrival**: Optimal route planning between two specific cities
- **📍 Detailed Itineraries**: Complete day-by-day view with POIs, costs, and timings
- **🌤️ Weather Integration**: 5-day forecasts to optimize activities
- **🎨 Smart POIs**: Over 3000 attractions from OpenStreetMap categorized by interests
- **🚆 Trenitalia API**: Real train schedules and connections
- **💰 Cost Estimation**: Automatic daily and total budget calculation

## 🏗️ Architecture

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

## 🚀 Installation and Setup

### 1. Clone and Setup

```bash
git clone https://github.com/TommasoAiello08/SE_Proj-Train_Trip_Planner.git
cd SEProejct
python3 -m venv .venv
pip install -r requirements.txt
```

### 2. Start System (Automatic) ⚡

```bash
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows
./start.sh
```

The `start.sh` script automatically:
- 🔄 Terminates previous processes on ports 5001 and 8080
- 🚀 Starts Flask backend (port 5001)
- 🌐 Starts frontend HTTP server (port 8080)
- 🔗 Automatically opens browser at **http://localhost:8080/map_planner.html**
- 📝 Logs available in `/tmp/backend.log` and `/tmp/frontend.log`

**To stop the servers:**
```bash
./stop.sh
```

### 3. Manual Start (Optional)

If you prefer to start manually (2 terminals):

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

Open in browser: **http://localhost:8080/map_planner.html**

## 🎮 How to Use

### "Departure Only" Mode 🧠
1. Click **"🧠 Departure Only"** (default mode)
2. Click a city on the map (turns **green**)
3. Select departure date and duration (1-5 days)
4. Choose interests (optional): art, history, nature, food, sea, mountain
5. Click **"🔍 Plan Trip"**
6. View detailed itinerary below the map

### "Departure + Arrival" Mode 🎯
1. Click **"🎯 Departure + Arrival"**
2. Click departure city (**green**) then arrival city (**red**)
3. Set parameters and click **"🔍 Plan Trip"**
4. System plans optimal route between the two cities

### Itinerary Result

The itinerary shows for each day:
- 🏙️ **City and date**
- 🚂 **Train journey** (duration and estimated times)
- 🎯 **Daily activities** with:
  - Attraction name and type
  - ⏱️ Visit duration
  - 💰 Entrance cost
  - ⭐ Quality rating
- 📊 **Daily summary**: available hours and total cost

## 🔧 Troubleshooting

### ❌ Error: "Failed to fetch" or CORS errors

**Quick Solution:**
```bash
./stop.sh && ./start.sh
```

**Cause**: Frontend not served via HTTP or backend stopped

**Manual Solution**:
1. Verify **both servers** are running:
   - **Backend**: port 5001
   - **Frontend**: port 8080
2. Access: **http://localhost:8080/map_planner.html** (not file://)
3. Check logs: `/tmp/backend.log` and `/tmp/frontend.log`
4. Reload browser page (F5)

**⚠️ Important**: DO NOT open the HTML file directly with double-click. Always use `./start.sh` to start the system.

### If port 5001 or 8080 is busy

```bash
./stop.sh  # Automatically terminates processes on ports 5001 and 8080
./start.sh # Restart system
```

**Manual check:**
```bash
lsof -i :5001  # Backend
lsof -i :8080  # Frontend
```

### Map doesn't load 106 cities

1. Check backend logs: must show `✅ Database loaded: 106 cities`
2. Check browser console (F12) for API errors
3. Manual endpoint test: `curl http://localhost:5001/api/cities`
4. If you see fewer than 106 cities, regenerate database:
   ```bash
   python scripts/build_complete_database.py
   ```

### Dependency errors

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

## 🛠️ Useful Scripts

### Start/Stop System
```bash
source .venv/bin/activate
./start.sh  # Start backend + frontend + open browser
./stop.sh   # Stop all servers
```

### Regenerate Database from OSM
```bash
python scripts/build_complete_database.py
# Downloads 107 Italian provinces with ~30 POIs each
# Time: ~5-6 minutes with automatic retry
```

### Verify System Health
```bash
curl http://localhost:5001/api/health
# Output: {"message":"OK","status":"healthy"}

curl http://localhost:5001/api/cities | python -m json.tool | head -20
# Verify loaded cities
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
  "interests": ["art", "history"]
}
```

## 📊 Algorithms

- **Dijkstra**: Optimal path between cities
- **Knapsack**: Daily POI selection
- **Greedy**: Attraction scoring
- **Haversine**: Distance calculation

## 🔑 APIs Used

- **Trenitalia ViaggiaTreno**: Train schedules (public)
- **OpenStreetMap**: Geocoding and POIs
- **OpenWeatherMap**: Weather forecasts

## 📝 License

MIT License

---

**Happy travels! 🚂🇮🇹**
