# Italian Train Trip Planner

Multi-day train travel planner for Italy using Dynamic Programming optimization, Trenitalia API integration, and OpenStreetMap POI curation.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Cities](https://img.shields.io/badge/cities-106-green.svg)
![POIs](https://img.shields.io/badge/POIs-2000+-orange.svg)
![Status](https://img.shields.io/badge/status-beta-yellow.svg)

## Features

- **Interactive Map**: Visual selection of 106 Italian provinces with train connections
- **Dynamic Programming Route Optimization**: 
  - Multi-day itinerary optimization balancing exploration, comfort, and travel time
  - Automatic intermediate city selection for long-distance trips
  - MAX 2 consecutive days per city for diverse itineraries
  - Score-based city ranking considering user interests, attractions, and geographic alignment
- **Dual Planning Modes**:
  - Smart Open: System suggests destinations from starting city
  - Smart Fixed: Optimal route planning between departure and arrival with intelligent waypoints
- **Curated POIs**: 
  - 20 attractions per city from OpenStreetMap (2120 total POIs)
  - Category diversity algorithm ensures variety (natura, cultura, arte, storia, etc.)
  - Note: OSM data shows limited rating variance (mean 7.58, 99% clustered at 7-8)
- **Train Integration**: 
  - Trenitalia API with time-aware search (9:00 day 1, 13:00+ subsequent days)
  - Running clock system (8:00-21:00) for realistic daily schedules
  - Aggressive caching to maintain ~20-30s response times
- **Cost Estimation**: Day-by-day budget including trains, attractions, and meals

## Architecture

```
SEProejct/
├── frontend/
│   ├── backend_server.py       # Flask API server (port 5001)
│   └── map_planner.html        # Interactive web interface
├── src/
│   ├── dp_itinerary_planner.py # Dynamic Programming route optimizer
│   ├── train_pathfinder.py     # BFS algorithm for real train routes
│   ├── city_database.py        # 106 cities with OSM on-demand loading
│   ├── osm_provider.py         # OpenStreetMap POI curation
│   ├── weather_provider.py     # Weather API (prepared, not actively used)
│   └── apitr.py                # Trenitalia API wrapper
├── tests/                      # Test suite (see tests/README.md)
│   ├── test_integration.py     # End-to-end system test
│   ├── test_lungo.py           # Long-distance routes test
│   └── test_completo.py        # PathFinder multi-route test
├── cache/
│   └── osm/                    # 106 city POI caches (20 curated each)
├── data/
│   ├── cities_database.json    # 106 Italian provinces metadata
│   └── provinces_static.json   # Fallback static data
├── docs/                       # Technical documentation
└── scripts/                    # Utility scripts for data generation
```

### Algorithm Overview

The system uses a hybrid 6-step algorithmic pipeline:

1. **Route-Based Candidate Selection**: Filters 106 cities to ~25-35 candidates using detour penalty formula favoring cities along the direct path
2. **Fast Train Matrix Building**: Uses geometric fallback (distance/100 km/h) during planning phase for speed
3. **Dynamic Programming Optimization**: Computes optimal city sequence by evaluating STAY (comfort bonus) vs MOVE (exploration bonus minus travel cost) transitions, with daily constraints ensuring realistic schedules
4. **Greedy Knapsack POI Selection**: Selects 2-3 attractions per day based on interest matching and ratings, respecting running clock constraint (8:00-21:00)
5. **Train Enrichment with Real API Data**: Queries Trenitalia API for EACH route segment with 3-level fallback (direct search → alternative routes → geometric estimate)
6. **Coverage Reporting**: Tracks percentage of routes with real train data vs estimates

**Key Parameters:**
- MAX_DAYS_PER_CITY = 2 (forces diverse itineraries)
- MIN_STAY_HOURS = 2 (minimum exploration time)
- MAX_TRAIN_HOURS_PER_DAY = 12
- Exploration bonus: +50 points
- Stay bonus: +30 points
- Travel penalty: -5 per hour

**Performance:**
- Planning phase: ~5-10 seconds (geometric estimates)
- Train enrichment: ~6 seconds per route segment
- Total: ~20-40 seconds for 2-5 day trips

## Installation and Setup

### 1. Clone and Setup

```bash
git clone https://github.com/TommasoAiello08/SE_Proj-Train_Trip_Planner.git
cd SEProejct
python3 -m venv .venv
pip install -r requirements.txt
```

### 2. Start System

```bash
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows
./start.sh
```

The script automatically starts Flask backend (port 5001) and frontend HTTP server (port 8080), then opens browser at http://localhost:8080/map_planner.html

**To stop:** `./stop.sh`

### 3. Manual Start (Optional)

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

## Usage

### "Departure Only" Mode
1. Click "Departure Only" (default)
2. Select city on map (green marker)
3. Choose date, duration (1-7 days), and interests
4. Click "Plan Trip"

### "Departure + Arrival" Mode
1. Click "Departure + Arrival"
2. Select departure (green) and arrival (red) cities
3. Set parameters and plan trip
4. System uses DP to find optimal route with intermediate stops

Example: Trieste → Palermo (5 days) generates diverse route visiting 5 unique cities

### Result Display

Each day shows:
- City and date
- Train details (departure, duration, arrival)
- Activities with timing, costs, and ratings
- Daily summary with total cost
- Route visualization on map

## Known Issues and Limitations

**Beta Status**: This project is in beta. Production deployment would require:
- Higher quality data sources (current OSM data: mean rating 7.58, variance 0.26, 99% clustered at 7-8)
- More rigorous algorithm validation and parameter tuning
- Architectural redesign for scalability

**Computation Speed**: Response times ~20-30 seconds achieved through aggressive caching. Initial implementation with real-time API queries took several minutes.

**DP Convergence**: Algorithm required careful parameter tuning:
- Too high exploration bonus → zig-zag routes
- Too low exploration bonus → staying in one city
- Final parameters: exploration +50, stay +30, travel -5×hours

**Scalability**: Not designed for multi-country expansion:
- Would require integrating multiple national APIs
- Exponentially larger datasets
- Computation times exceeding acceptable web thresholds

**Data Quality**: OSM data limitations affect attraction differentiation between cities

## Troubleshooting

### Error: "Failed to fetch" or CORS errors

**Quick Solution:**
```bash
./stop.sh && ./start.sh
```

**Cause**: Frontend not served via HTTP or backend stopped

**Manual Solution**:
1. Verify both servers running (ports 5001 and 8080)
2. Access: http://localhost:8080/map_planner.html (not file://)
3. Check logs: /tmp/backend.log and /tmp/frontend.log

**Important**: DO NOT open HTML file directly. Always use ./start.sh

### Port conflicts

```bash
./stop.sh  # Terminates processes on ports 5001 and 8080
./start.sh
```

### Map doesn't load cities

1. Check backend logs: must show "Database loaded: 106 cities"
2. Check browser console (F12) for errors
3. Test endpoint: `curl http://localhost:5001/api/cities`

## Useful Scripts

## Useful Scripts

### Start/Stop
```bash
./start.sh  # Start backend + frontend + open browser
./stop.sh   # Stop all servers
```

### Regenerate OSM Cache
```bash
python scripts/pull_all_osm_data.py
# Downloads POI data for all 106 cities
# Time: ~8-10 minutes
```

### Verify Cache
```bash
ls cache/osm/*.json | wc -l  # Should show 106
```

### Health Check
```bash
curl http://localhost:5001/api/health
# Output: {"message":"OK","status":"healthy"}
```

## Contributors

- **Tommaso Aiello**: Core development, DP optimization, OSM integration
- **Alessandro**: Bug fixes and validation

## Project Info

Developed for Software Engineering course at Università degli Studi di Milano (2025/2026)

## License

MIT License

---

**Quick Start**: `source .venv/bin/activate && ./start.sh`

**Performance**: 5-day trip ~20-30 seconds with OSM cache
