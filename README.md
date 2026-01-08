# 🚂 Italian Train Trip Planner

Intelligent train travel planning system for Italy with **Dynamic Programming optimization**, Trenitalia API integration, OpenStreetMap POI curation, and real-time weather data.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Cities](https://img.shields.io/badge/cities-106-green.svg)
![POIs](https://img.shields.io/badge/POIs-2000+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **🗺️ Interactive Map**: Visual selection of **106 Italian provinces** with real-time train connections
- **🧠 Smart AI Planning with Dynamic Programming**: 
  - Multi-day route optimization with train schedule integration
  - **MAX 2 days per city** constraint for diverse itineraries
  - Automatic intermediate city selection for long-distance trips
  - Score-based city ranking considering interests, attractions, and travel efficiency
- **🎯 Dual Planning Modes**:
  - **Smart Open**: System suggests best destinations from starting city
  - **Smart Fixed**: Optimal route planning between departure and arrival cities with intelligent waypoints
- **📍 Curated POIs**: 
  - **20 attractions per city** carefully selected from 28+ OpenStreetMap categories
  - Category diversity: natura, cultura, arte, cibo, mare, montagna, storia, sport
  - Rating balance: mix of top-rated (10/9) and hidden gems (8/7)
- **🚆 Real Train Integration**: 
  - Trenitalia API with time-aware search (9:00 day 1, 13:00+ subsequent days)
  - Running clock system (8:00-21:00) for realistic daily schedules
  - Travel time + minimum stay constraints
- **🌤️ Weather Integration**: 5-day forecasts to optimize outdoor activities
- **💰 Smart Cost Estimation**: Day-by-day budget with trains, attractions, and meals
- **⚡ Performance Optimized**: 
  - OSM cache system for instant POI loading
  - Optimized DP parameters (35 candidates, 8 connections per city)
  - Realistic computation time estimation (~22-24s for 5-day trips)

## 🏗️ Architecture

```
SEProejct/
├── frontend/
│   ├── backend_server.py       # Flask API server (port 5001)
│   └── map_planner.html        # Interactive web interface with route visualization
├── src/
│   ├── dp_itinerary_planner.py # ⭐ NEW: Dynamic Programming route optimizer
│   ├── itinerary_planner.py    # Legacy greedy planner
│   ├── city_database.py        # 106 cities with OSM on-demand loading
│   ├── travel_graph.py         # Train connection graph
│   ├── osm_provider.py         # OpenStreetMap POI curation (20/city)
│   ├── weather_provider.py     # Weather API integration
│   └── apitr.py                # Trenitalia API wrapper
├── cache/
│   └── osm/                    # 106 city POI caches (20 curated each)
├── data/
│   ├── cities_database.json    # 106 Italian provinces metadata
│   └── provinces_static.json   # Fallback static data
└── scripts/
    ├── pull_all_osm_data.py    # Complete OSM cache refresh
    └── build_complete_database.py  # Database builder
```

### 🧮 Dynamic Programming Algorithm

The DP optimizer (`dp_itinerary_planner.py`) features:

- **State**: `dp[day][city]` = maximum score reaching city on given day
- **Transitions**: STAY (same city) vs MOVE (different city with train)
- **Constraints**:
  - `MAX_DAYS_PER_CITY = 2`: Forces diverse itineraries
  - `MIN_STAY_HOURS = 4`: Minimum stay after travel
  - `MAX_TRAIN_HOURS = 8`: Daily travel limit
- **Scoring**:
  - City attractions + interest match
  - Route-based candidate selection (favors cities along path)
  - Exploration bonus (50pts) vs Stay bonus (30pts)
  - Travel penalty (time × 5)
- **Features**:
  - Consecutive day tracking to enforce city limits
  - Knapsack POI selection with running clock (8:00-21:00)
  - Day-by-day schedule generation without duplicates

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
4. System uses **Dynamic Programming** to find optimal route with intermediate stops
5. **Example**: Trieste → Palermo (5 days) generates route like:
   - Day 1-2: Trieste (2 days, 20 POIs)
   - Day 3-4: Bologna or Rome (2 days, 20 POIs)  
   - Day 5: Palermo (1 day, 20 POIs)

### Itinerary Result

The itinerary shows for each day:
- 🏙️ **City and date**
- 🚂 **Train journey** (departure time, duration, arrival)
- 🎯 **Daily activities** with:
  - Attraction name, type, and category
  - ⏱️ Visit duration (3h per POI)
  - 💰 Entrance cost
  - ⭐ Quality rating (7-10)
  - 🕐 Start time in running clock (8:00-21:00)
- 📊 **Daily summary**: total POIs, available hours, and daily cost
- 🗺️ **Route visualization**: Red dotted line connecting cities on map

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

### Regenerate OSM Cache
```bash
python scripts/pull_all_osm_data.py
# Downloads fresh POI data for all 106 cities
# Each city: 20 curated POIs from 28+ categories
# Time: ~8-10 minutes with adaptive radius (15km → 25km → 35km)
# Output: cache/osm/*.json
```

### Verify Cache
```bash
ls cache/osm/*.json | wc -l  # Should show 106
cat cache/osm/roma.json | python -m json.tool | grep '"name"' | head -20
```

### Verify System Health
```bash
curl http://localhost:5001/api/health
# Output: {"message":"OK","status":"healthy"}

curl http://localhost:5001/api/cities | python -m json.tool | head -20
# Verify loaded cities
```

## 👥 Contributors

- **Tommaso Aiello**: Core development, DP optimization, OSM integration, POI curation
- **Alessandro**: Bug fixes, validation, and testing (branch fix/ale)

## 🎓 Project Info

Developed for **Software Engineering** course at Università degli Studi di Milano.

**Academic Year**: 2025/2026

## 📄 License

MIT License - see LICENSE file for details

---

**🚀 Quick Start**: 
```bash
source .venv/bin/activate && ./start.sh
```

**🐛 Troubleshooting**: If routes show empty days, restart system: `./stop.sh && ./start.sh`

**📈 Performance**: 5-day trip computation ~22-24 seconds with OSM cache

## 🆕 Recent Updates (January 2026)

### v2.0 - Dynamic Programming Revolution
- ✅ Complete DP-based route optimizer with multi-day support
- ✅ MAX_DAYS_PER_CITY constraint (max 2 days per location)
- ✅ OSM POI curation: 20 diverse attractions per city
- ✅ Running clock system (8:00-21:00) for realistic schedules
- ✅ Time-aware train search (9:00 day 1, 13:00+ subsequent days)
- ✅ Route visualization with red dotted lines on map
- ✅ Performance optimization (35 candidates, 8 connections)
- ✅ Category diversity: 8 categories with min 2 POIs each
- ✅ Rating balance: mix of 10/9 (top) and 8/7 (hidden gems)
- ✅ On-demand OSM enrichment for cities with missing POIs

### Known Limitations
- Long-distance routes (>1000 km) may take 30-40 seconds
- OSM cache recommended for all 106 cities (use `pull_all_osm_data.py`)
- Maximum trip duration: 30 days

---

**Happy travels! 🚂🇮🇹**
