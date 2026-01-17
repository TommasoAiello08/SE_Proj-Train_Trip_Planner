# 🚂 Italian Train Trip Planner

Multi-day train travel planner for Italy using **Dynamic Programming optimization**, **Trenitalia API integration**, and **OpenStreetMap POI curation**.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Cities](https://img.shields.io/badge/cities-106-green.svg)
![POIs](https://img.shields.io/badge/POIs-2000+-orange.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Algorithm Details](#-algorithm-details)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Capabilities

- **🗺️ Interactive Map Interface**: Visual selection of 106 Italian provinces with train connections
- **🧮 Dynamic Programming Route Optimization**: 
  - Multi-day itinerary optimization balancing exploration, comfort, and travel time
  - Automatic intermediate city selection for long-distance trips
  - **MAX 2 consecutive days per city** for diverse itineraries
  - Score-based city ranking considering user interests, attractions, and geographic alignment
  - Smart fallback for unreachable destinations with intermediate city selection

- **🎯 Dual Planning Modes**:
  - **Smart Open**: System suggests destinations from starting city
  - **Smart Fixed**: Optimal route planning between departure and arrival with intelligent waypoints

- **📍 Curated POIs**: 
  - **20 attractions per city** from OpenStreetMap (2,120 total POIs)
  - Category diversity algorithm ensures variety (natura, cultura, arte, storia, architettura, religione, intrattenimento, shopping)
  - Cached for instant access

- **🚆 Train Integration**: 
  - **Trenitalia API** with time-aware search (9:00 day 1, 13:00+ subsequent days)
  - Running clock system (8:00-21:00) for realistic daily schedules
  - Aggressive caching to maintain **~30-60s response times**
  - Smart train matrix building with destination guarantee

- **💰 Cost Estimation**: Day-by-day budget including trains, attractions, and meals

---

## 🚀 Quick Start

```bash
# 1. Clone and navigate
git clone https://github.com/TommasoAiello08/SE_Proj-Train_Trip_Planner.git
cd SEProejct

# 2. Setup environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Start system
./start.sh

# ✅ System will open in browser at http://localhost:8080
```

**To stop:** `./stop.sh`

---

## 🏗️ Architecture

### Project Structure

```
SEProejct/
├── frontend/
│   ├── backend_server.py       # Flask API server (port 5001)
│   └── map_planner.html        # Interactive web interface
│
├── src/
│   ├── dp_itinerary_planner.py # ⭐ Dynamic Programming route optimizer
│   ├── train_pathfinder.py     # BFS algorithm for real train routes
│   ├── city_database.py        # 106 cities with OSM on-demand loading
│   ├── osm_provider.py         # OpenStreetMap POI curation
│   ├── weather_provider.py     # Weather API (prepared, not actively used)
│   └── apitr.py                # Trenitalia API wrapper
│
├── tests/                      # Comprehensive test suite
│   ├── test_integration.py     # End-to-end system test
│   ├── test_lungo.py           # Long-distance routes test
│   └── test_completo.py        # PathFinder multi-route test
│
├── cache/
│   └── osm/                    # 106 city POI caches (20 curated each)
│
├── data/
│   ├── cities_database.json    # 106 Italian provinces metadata
│   └── provinces_static.json   # Fallback static data
│
├── scripts/                    # Utility scripts
│   └── pull_all_osm_data.py    # OSM cache regeneration
│
├── start.sh                    # Launch script
├── stop.sh                     # Shutdown script
└── requirements.txt            # Python dependencies
```

### System Flow

```
User Request → Flask API → DP Planner → Train Matrix → Route Optimization
                    ↓
              City Database → OSM Provider → Cached POIs
                    ↓
              Train API → Trenitalia → Cached Connections
                    ↓
              Schedule Generator → Daily Itinerary → JSON Response
```

---

## 🧮 Algorithm Details

### Overview

The system uses a **6-step algorithmic pipeline** combining Dynamic Programming, constraint satisfaction, and greedy optimization:

```
1. Route-Based Candidate Selection (35 from 106 cities)
2. Time-Aware Train Matrix Building (with destination guarantee)
3. Dynamic Programming Optimization (STAY vs MOVE decisions)
4. Day Allocation (consecutive counting)
5. Detailed Schedule Generation (running clock + knapsack POI selection)
6. Smart Fallback (geographic intermediate cities for unreachable destinations)
```

### Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `MAX_DAYS_PER_CITY` | 2 | Force diverse itineraries |
| `MIN_STAY_HOURS` | 2 | Minimum exploration time per city |
| `MAX_TRAIN_HOURS_PER_DAY` | 12 | Maximum daily travel time |
| `HOURS_PER_DAY` | 13 | Operating window (8:00-21:00) |
| `MAX_CANDIDATES` | 35 | Cities considered in optimization |
| `MAX_CONNECTIONS_PER_CITY` | 12 | Train routes per city (performance) |
| `TRAIN_BUFFER_HOURS` | 0.5 | Station access/waiting time |

### Scoring System

**City Score:**
```python
base_score = num_attractions × 10
interest_match = num_matching_categories × 15
route_bonus = max(0, 200 - (detour / 10))
total = base_score + interest_match + route_bonus
```

**DP Transition Scores:**

- **STAY** (same city):
  - `city_score × 0.7 + 30` (stay bonus)
  - Blocked after 2 consecutive days
  - Total: ~100-150 points

- **MOVE** (different city):
  - `city_score + 50 - (travel_time × 5)`
  - +50 exploration bonus
  - -5 per hour travel penalty
  - Total: ~100-200 for nearby, ~50-100 for distant

### Step-by-Step Algorithm

#### 1. Candidate City Selection

**Goal**: Reduce search space from 106 to ~35 cities

**Strategy**: Route-based scoring (not just proximity)

```python
# Calculate detour for each city
detour = (dist_start_to_city + dist_city_to_end) - dist_start_to_end
route_bonus = max(0, 200 - (detour / 10))

# Cities along path get higher bonus
# Example: Trieste → Rome → Palermo
#   Bologna: 20km detour → 198 bonus
#   Milan: 250km detour → 175 bonus
```

**Always includes**: Start city, end city (guaranteed in top-35)

#### 2. Train Matrix Building

**Goal**: Build train connections for all (city, city, day) combinations

**Time-Aware Search**:
- **Day 1**: Searches trains from 9:00 AM (realistic start)
- **Day 2+**: Searches trains from 1:00 PM (assumes previous day arrival)

**Destination Guarantee** ⭐ (v2.1 fix):
```python
# CRITICAL: Always include end city in connections
candidate_dests = select_relevant_destinations(
    origin, 
    candidates, 
    MAX_CONNECTIONS_PER_CITY,
    force_include=[end]  # Ensures destination reachable
)
```

**Output Structure**:
```python
train_matrix[day][origin][dest] = {
    'departure': '14:25',
    'arrival': '16:40',
    'travel_time': 2.25,  # hours
    'train_number': 'FR 9315',
    'price': 35.0
}
```

#### 3. Dynamic Programming Optimization

**State Definition**:
```python
dp[day][city] = maximum_score reaching city on given day
prev[day][city] = previous_city (for backtracking)
consecutive_days[day][city] = consecutive days in same city
```

**Transitions**:

**Option A - STAY** (remain in same city):
```python
if consecutive_days[d][A] < MAX_DAYS_PER_CITY:
    stay_score = dp[d][A] + city_score(A) × 0.7 + 30
    consecutive_days[d+1][A] = consecutive_days[d][A] + 1
else:
    # BLOCKED: Already 2 days here, must move
```

**Option B - MOVE** (travel to different city):
```python
# Constraints:
# 1. Train exists: train_matrix[d+1][A][B]
# 2. Travel + stay fits: travel_time + MIN_STAY ≤ HOURS_PER_DAY
# 3. Travel limit: travel_time ≤ MAX_TRAIN_HOURS_PER_DAY

move_score = dp[d][A] + city_score(B) + 50 - (travel_time × 5)
consecutive_days[d+1][B] = 1  # Reset counter
```

**Initialization**:
```python
dp[1][start] = score(start_city)
consecutive_days[1][start] = 1
```

**Backtracking**:
```python
# Find best ending state
best_day = -1
for d in range(num_days, 0, -1):
    if end in dp[d]:
        best_day = d
        break

# Reconstruct route
route = []
current = end
for d in range(best_day, 0, -1):
    route.append(current)
    current = prev[d][current]
route.reverse()
```

#### 4. Smart Fallback (v2.1)

**Triggered when**: DP cannot reach destination (best_day == -1)

**Strategy**: Find geographic intermediate cities

```python
# For each candidate city:
dist_start_to_city = haversine(start, city)
dist_city_to_end = haversine(city, end)
dist_start_to_end = haversine(start, end)

detour = (dist_start_to_city + dist_city_to_end) - dist_start_to_end

if detour < 150km:  # Max 150km detour tolerance
    intermediate_cities.append((city, dist_start_to_city))

# Sort by distance from start
intermediate_cities.sort(by_distance)

# Build route respecting MAX_DAYS_PER_CITY
route = [start] × 2  # Start city (2 days max)
for city in intermediate_cities:
    if days_remaining > 0:
        route += [city] × min(2, days_remaining)
route += [end] × remaining_days
```

**Example**: Trieste → Siracusa (1,500km, unreachable in 5 days)
- Fallback: `['Trieste', 'Trieste', 'Gorizia', 'Gorizia', 'Siracusa']`
- ✅ 3 unique cities vs. ❌ 2 cities without fallback

#### 5. Day Allocation

**Simple counting** of consecutive occurrences:

```python
route = ['Trieste', 'Trieste', 'Bologna', 'Bologna', 'Palermo']
allocation = {'Trieste': 2, 'Bologna': 2, 'Palermo': 1}
```

#### 6. Detailed Schedule Generation

**Running Clock System** (8:00 AM - 9:00 PM):

```python
for day, city in enumerate(route):
    clock = 8.0  # Start at 8:00 AM
    
    # Add train travel time if arriving today
    if moving_from_different_city:
        train = get_train_for_day(day)
        clock += train['travel_time']
    
    # Knapsack POI selection
    available_time = 21.0 - clock  # Until 9 PM
    max_pois = int(available_time / 3.0)  # 3 hours per POI
    
    pois = select_best_pois(city, max_pois, interests)
    
    # Track used POIs to avoid duplicates across days
    for poi in pois:
        used_attractions[city].add(poi['name'])
```

**POI Selection** (Greedy Knapsack):
- **Duration**: 3 hours per attraction
- **Selection**: Highest rated POIs matching user interests
- **Diversity**: 20 curated POIs per city with category balance
- **Deduplication**: Never repeat POI across multiple days in same city

### Example Execution: Trieste → Palermo (5 days)

**Input:**
- Start: Trieste (northeast Italy)
- End: Palermo (Sicily)
- Days: 5
- Distance: ~1,500 km

**Step 1 - Candidates** (top 35):
```
Bologna:  detour=20km,  route_bonus=198, score=315
Firenze:  detour=40km,  route_bonus=196, score=308
Roma:     detour=60km,  route_bonus=194, score=320
Napoli:   detour=80km,  route_bonus=192, score=298
Milano:   detour=250km, route_bonus=175, score=285
```

**Step 2 - Train Matrix** (sample entries):
```
train_matrix[1]['Trieste']['Bologna'] = {travel_time: 4.0h, departure: '09:00'}
train_matrix[2]['Trieste']['Bologna'] = {travel_time: 4.0h, departure: '13:00'}
train_matrix[3]['Bologna']['Roma'] = {travel_time: 2.5h, departure: '13:00'}
train_matrix[4]['Roma']['Napoli'] = {travel_time: 1.5h, departure: '13:00'}
```

**Step 3 - DP Execution**:

| Day | Current City | Option | Score | Decision |
|-----|-------------|---------|-------|----------|
| 1 | Trieste | Initialize | 120 | START |
| 2 | Trieste | STAY (1→2) | 204 | ✅ Stay |
| 2 | Bologna | MOVE (1→2) | 190 | ❌ Lower score |
| 3 | Trieste | STAY (2→3) | - | ❌ BLOCKED (2 days) |
| 3 | Bologna | MOVE (2→3) | 360 | ✅ Move |
| 4 | Bologna | STAY (3→4) | 450 | 🔸 Option |
| 4 | Roma | MOVE (3→4) | 485 | ✅ Better |
| 5 | Roma | STAY (4→5) | - | ❌ Need Palermo |
| 5 | Palermo | MOVE (4→5) | 580 | ✅ Destination |

**Generated Route**:
```python
['Trieste', 'Trieste', 'Bologna', 'Roma', 'Palermo']
```

**Step 4 - Allocation**:
```python
{'Trieste': 2, 'Bologna': 1, 'Roma': 1, 'Palermo': 1}
```

**Step 5 - Schedule**:
```
Day 1: Trieste
  08:00 - Start day
  08:00-11:00: Grotta Gigante (3h, €10)
  11:00-14:00: Castello di Miramare (3h, €8)
  14:00-17:00: Piazza Unità d'Italia (3h, free)
  Cost: €18 + €15 meals = €33

Day 2: Trieste
  08:00 - Start day
  08:00-11:00: Riserva Naturale (3h, €8)
  11:00-14:00: Teatro Romano (3h, €5)
  14:00-17:00: Faro della Vittoria (3h, free)
  Cost: €13 + €15 meals = €28

Day 3: Bologna (Train: Trieste → Bologna, 4.0h)
  08:00 + 4.0 = 12:00 - Arrival
  12:00-15:00: Basilica San Petronio (3h, €5)
  15:00-18:00: Le Due Torri (3h, €8)
  18:00-21:00: Piazza Maggiore (3h, free)
  Cost: €35 train + €13 + €15 meals = €63

Day 4: Roma (Train: Bologna → Roma, 2.5h)
  08:00 + 2.5 = 10:30 - Arrival
  10:30-13:30: Colosseo (3h, €16)
  13:30-16:30: Fontana di Trevi (3h, free)
  16:30-19:30: Piazza Navona (3h, free)
  Cost: €25 train + €16 + €15 meals = €56

Day 5: Palermo (Train: Roma → Palermo, 8.0h)
  08:00 + 8.0 = 16:00 - Arrival
  16:00-19:00: Cappella Palatina (3h, €10)
  Cost: €80 train+ferry + €10 + €15 meals = €105

Total Trip Cost: €285
```

### Performance & Complexity

**Time Complexity:**
- Candidate selection: O(C log C) where C=106
- Train matrix: O(D × N × K) where D=days, N=35, K=12 ≈ 2,100 API calls
- DP: O(D × N²) = O(5 × 35²) ≈ 6,000 operations
- **Total**: ~30-60 seconds for 5-day trip

**Optimizations:**
1. ✅ Pre-calculated distances (1 call vs 212)
2. ✅ Cached city scores (reuse in DP)
3. ✅ Limited search space (35 candidates vs 106)
4. ✅ Smart connection selection (12 per city vs all)
5. ✅ Destination guarantee (ensures reachability)

---

## 📥 Installation

### Prerequisites

- Python 3.10+
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Step-by-Step

```bash
# 1. Clone repository
git clone https://github.com/TommasoAiello08/SE_Proj-Train_Trip_Planner.git
cd SEProejct

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate environment
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify OSM cache (should show 106 files)
ls cache/osm/*.json | wc -l

# 6. Test backend
python frontend/backend_server.py
# Should show: "✅ Database loaded: 106 cities"
# Press Ctrl+C to stop

# 7. Launch system
./start.sh
```

### Manual Start (Alternative)

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
python frontend/backend_server.py
# Runs on port 5001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python3 -m http.server 8080
# Serves map_planner.html
```

**Open browser**: http://localhost:8080/map_planner.html

---

## 📖 Usage Guide

### Mode 1: Departure Only (Round Trip)

1. Click **"Departure Only"** button (default mode)
2. **Select starting city** on map (green marker appears)
3. Configure trip:
   - **Date**: Departure date
   - **Duration**: 1-7 days
   - **Interests**: Select categories (art, history, nature, etc.)
4. Click **"Plan Trip"**
5. Wait ~20-40 seconds for optimization

**Use Case**: "I'm in Rome, plan me a 3-day trip"

### Mode 2: Departure + Arrival (Fixed Route)

1. Click **"Departure + Arrival"** button
2. **Select departure city** (green marker)
3. **Select arrival city** (red marker)
4. Configure trip parameters
5. Click **"Plan Trip"**

**Example**: Trieste → Palermo (5 days)
- System finds optimal route with intermediate cities
- Respects MAX_DAYS_PER_CITY constraint
- Balances exploration vs travel time

**Use Case**: "I need to go from Milan to Naples in 4 days, optimize my route"

### Understanding Results

Each day displays:

```
📅 Day 1 - Milano (2024-06-15)

🚂 Train: 09:00 - 11:30 (2h 30m) → Bologna
    Train #FR9315 | Cost: €35

🎯 Activities:
  • 12:00-15:00  Basilica di San Petronio
    💰 €5 | ⭐ 8/10 | 🏛️ Religione
  
  • 15:00-18:00  Le Due Torri
    💰 €8 | ⭐ 8/10 | 🏰 Storia
  
  • 18:00-21:00  Piazza Maggiore
    💰 Free | ⭐ 8/10 | 🎨 Cultura

💵 Daily Total: €63 (€35 train + €13 attractions + €15 meals)
```

**Map Visualization**:
- Green line: Train routes
- Numbered markers: Cities in order
- Info boxes: City details on hover

---

## 🧪 Testing

### Test Suite Overview

```bash
# Activate environment
source .venv/bin/activate

# Run all tests
python tests/test_integration.py
python tests/test_lungo.py
python tests/test_completo.py
```

### Test Files

#### `test_integration.py` ⭐ **System Integration Test**
- **Route**: Milano → Bologna (2 days)
- **Validates**: End-to-end DP + PathFinder + POI generation
- **Checks**: Real train data coverage, fallback usage

**Expected Output**:
```
✅ Itinerario generato: 2 giorni
📈 Copertura dati reali: 1/1 tratte (100%)
🎉 SUCCESSO: Sistema funzionante!
```

#### `test_lungo.py` ⭐ **Long-Distance Test**
- **Route**: Milano → Napoli (4 days)
- **Validates**: Multi-city routes, alternative paths, transfers
- **Metrics**: Success rate, real data percentage

**Expected Output**:
```
📊 STATISTICHE:
  ✅ Treni reali: 2/3 (67%)
  🔄 Con cambio: 1
  ⚠️  Stime: 1/3 (33%)
```

#### `test_completo.py` **PathFinder Multi-Route**
- **Routes**: 9 common Italian routes
- **Validates**: Train API across various distances
- **Metrics**: Success percentage, duration accuracy

**Routes Tested**:
```
✅ Milano → Bologna
✅ Milano → Roma
✅ Bologna → Firenze
✅ Roma → Napoli
✅ Milano → Venezia
⚠️ Milano → Palermo (fallback)
...
```

### Other Tests

- `test_percorsi.py`: Short routes (<300km)
- `test_fr.py`: Frecciarossa train debugging
- `test_oggi.py`: Current date/time testing
- `test_orari.py`: Various time slots (6:00-18:00)

---

## 🔧 Troubleshooting

### Error: "Failed to fetch" or CORS errors

**Quick Fix:**
```bash
./stop.sh && ./start.sh
```

**Root Cause**: Frontend not served via HTTP or backend stopped

**Manual Fix**:
1. Verify both servers running:
   ```bash
   curl http://localhost:5001/api/health
   curl http://localhost:8080/map_planner.html
   ```
2. Check logs:
   ```bash
   tail -f /tmp/backend.log
   tail -f /tmp/frontend.log
   ```

⚠️ **IMPORTANT**: Never open `map_planner.html` directly with `file://`. Always use `./start.sh` or HTTP server.

### Port Conflicts

**Symptom**: "Address already in use"

**Solution**:
```bash
./stop.sh  # Kills processes on ports 5001 and 8080
./start.sh
```

**Manual Check**:
```bash
lsof -ti:5001  # Check backend port
lsof -ti:8080  # Check frontend port
```

### Map Doesn't Load Cities

**Checks**:
1. Backend logs show "✅ Database loaded: 106 cities"
2. Browser console (F12) has no errors
3. Test endpoint:
   ```bash
   curl http://localhost:5001/api/cities
   # Should return JSON array with 106 cities
   ```

**Fix**: Restart backend:
```bash
pkill -f backend_server
python frontend/backend_server.py
```

### Slow Response Times (>60s)

**Causes**:
- OSM cache missing
- Train API rate limiting
- Network latency

**Solutions**:
```bash
# 1. Verify OSM cache
ls cache/osm/*.json | wc -l  # Should be 106

# 2. Regenerate cache if needed
python scripts/pull_all_osm_data.py  # ~8-10 minutes

# 3. Check network
ping api.openstreetmap.org
```

### Route Returns Only 2 Cities

**Problem** (Fixed in v2.1): DP cannot reach destination

**Diagnosis**:
```bash
# Check logs for fallback trigger
grep "FALLBACK TRIGGERED" /tmp/backend.log
grep "NEVER - this is the problem" /tmp/backend.log
```

**Cause**: Destination not in train matrix connections

**Solution** (already implemented):
- Force-include destination in all city connections
- Relaxed constraints: MIN_STAY=2h, MAX_TRAIN=12h
- Smart fallback with geographic intermediates

**If still occurs**: Increase `MAX_CONNECTIONS_PER_CITY` in `src/dp_itinerary_planner.py`:
```python
self.MAX_CONNECTIONS_PER_CITY = 15  # From 12
```

### "No trains found" for Future Dates

**Limitation**: Trenitalia API only returns data for current/near-future dates

**Solution**: Use recent dates or `datetime.now()` in tests

### Empty POI Lists

**Check OSM cache**:
```bash
cat cache/osm/roma.json | jq '.pois | length'
# Should show 20
```

**Regenerate if needed**:
```bash
python scripts/pull_all_osm_data.py
```

---

## 🛠️ Useful Scripts

### Start/Stop

```bash
./start.sh   # Launch backend + frontend + browser
./stop.sh    # Terminate all services
```

### OSM Cache Management

```bash
# Regenerate all POI caches (~8-10 minutes)
python scripts/pull_all_osm_data.py

# Verify cache integrity
ls cache/osm/*.json | wc -l  # Should be 106

# Check specific city
cat cache/osm/milano.json | jq '.pois | length'
```

### Health Checks

```bash
# Backend health
curl http://localhost:5001/api/health
# {"message":"OK","status":"healthy"}

# List available cities
curl http://localhost:5001/api/cities | jq 'length'
# 106

# Test planning endpoint
curl -X POST http://localhost:5001/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "smart_fixed",
    "start_city": "Milano",
    "end_city": "Bologna",
    "start_date": "2026-02-01",
    "duration": 3,
    "interests": ["history", "art"]
  }'
```

### Development

```bash
# Run with debug logging
python frontend/backend_server.py 2>&1 | grep -E "(DEBUG|ERROR)"

# Monitor logs in real-time
tail -f /tmp/backend.log

# Clear caches (use cautiously)
rm -rf cache/train_cache.json
rm -rf cache/osm/*.json  # Will need regeneration
```

---

## 📊 Known Limitations

### Beta Status

This project is in **production-ready beta**. Future improvements:

1. **Data Quality**: OSM data shows limited rating variance (mean 7.58, 99% clustered 7-8)
2. **Multi-Country**: Not designed for cross-border expansion (requires multiple national APIs)
3. **Scalability**: Optimized for 106 Italian cities; larger datasets need architectural changes
4. **Real-Time**: Train data depends on Trenitalia API availability and freshness

### Performance

- **Response time**: 30-60 seconds for 5-day trips (with cache)
- **Cold start**: Up to 2-3 minutes if cache empty
- **API calls**: ~2,100 train queries for 5-day trip (35 candidates × 12 connections × 5 days)

### Algorithm Convergence

Required careful parameter tuning:
- **Too high exploration bonus** → zigzag routes
- **Too low exploration bonus** → staying in one city  
- **Final balance**: exploration +50, stay +30, travel -5/hour

---

## 👥 Contributing

### Bug Reports

Found a bug? Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Logs from `/tmp/backend.log`

### Feature Requests

Suggest improvements via GitHub Issues. Include:
- Use case description
- Expected behavior
- Acceptance criteria

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/SE_Proj-Train_Trip_Planner.git
cd SEProejct

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
python tests/test_integration.py

# Commit with descriptive message
git commit -m "feat: add support for multi-day stays"

# Push and create PR
git push origin feature/your-feature-name
```

### Code Style

- Python: PEP 8 compliance
- Comments: Docstrings for all functions
- Type hints: Encouraged but not required

---

## 📜 License

**MIT License**

Copyright (c) 2026 Tommaso Aiello

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 📝 Project Info

**Course**: Software Engineering  
**University**: Università degli Studi di Milano  
**Academic Year**: 2025/2026  
**Developers**: 
- Tommaso Aiello (Lead Developer)
- Alessandro (Testing & Validation)

**Repository**: https://github.com/TommasoAiello08/SE_Proj-Train_Trip_Planner  
**Documentation**: This README (comprehensive guide)  
**Status**: Production-Ready Beta v2.1

---

## 🎯 Quick Reference

**Start System**: `./start.sh`  
**Stop System**: `./stop.sh`  
**Test System**: `python tests/test_integration.py`  
**Regenerate Cache**: `python scripts/pull_all_osm_data.py`  
**Check Health**: `curl http://localhost:5001/api/health`  

**Performance**: 5-day trip in ~30-60 seconds  
**Cities**: 106 Italian provinces  
**POIs**: 2,120 curated attractions  
**Algorithm**: Dynamic Programming with constraint satisfaction  

---

**🚂 Happy Planning! 🇮🇹**
