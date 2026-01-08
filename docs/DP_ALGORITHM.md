# 🧮 Dynamic Programming Algorithm

## Overview

The DP Itinerary Planner (`src/dp_itinerary_planner.py`) implements a sophisticated multi-day route optimization algorithm that balances train schedules, city attractions, and travel constraints.

## Algorithm Steps

### Step 1: Candidate City Selection

**Function**: `_select_candidate_provinces()`

**Strategy**: Route-based scoring (not just proximity to start)

```python
# For each city, calculate:
detour = (dist_from_start + dist_from_end) - total_distance
route_bonus = max(0, 200 - (detour / 10))

# Cities along the path get higher bonus
# Example: Trieste → Rome → Palermo
#   Bologna: small detour → high bonus (180-200)
#   Milan: large detour → low bonus (50-100)
```

**Parameters**:
- `MAX_CANDIDATES = 35`: Top cities considered
- Pre-calculates start→end distance once (optimization)

### Step 2: Train Matrix Building

**Function**: `_build_train_matrix()`

**Time-aware search**:
- **Day 1**: Searches trains from 9:00 AM
- **Day 2+**: Searches trains from 1:00 PM (assumes arrival previous day)

**Caching**: Train connections cached by `(origin, destination, date)`

**Output**: 
```python
train_matrix[day][from_city][to_city] = {
    'departure': '14:25',
    'arrival': '16:40',
    'travel_time': 2.25,  # hours
    'train_number': 'FR 9315'
}
```

### Step 3: Dynamic Programming Optimization

**Function**: `_dp_route_optimization()`

**State Definition**:
```python
dp[day][city] = maximum score reaching city on given day
prev[day][city] = previous city (for backtracking)
consecutive_days[day][city] = consecutive days in same city
```

**Transitions**:

#### Option 1: STAY (same city)
```python
# Condition: consecutive_days[city] < MAX_DAYS_PER_CITY (2)
stay_score = dp[d][A] + city_score(A) * 0.7 + 30
# Bonus 30 points for staying (saves travel)
# BUT blocked if already 2 days in city
```

#### Option 2: MOVE (different city)
```python
# Conditions:
# 1. Train exists: A → B on day d+1
# 2. travel_time + MIN_STAY_HOURS <= HOURS_PER_DAY (10h)
# 3. travel_time <= MAX_TRAIN_HOURS_PER_DAY (8h)

new_score = dp[d][A] + city_score(B) + exploration_bonus - travel_penalty
exploration_bonus = 50  # Encourages visiting new cities
travel_penalty = travel_time * 5  # Penalizes long trains
```

**Initialization**:
```python
dp[1][start] = score(start_city)
consecutive_days[1][start] = 1
```

**Backtracking**:
```python
# Start from end city at day N, follow prev[] pointers
route = []
current = end_city
for d in range(num_days, 0, -1):
    route.append(current)
    current = prev[d][current]
route.reverse()
# Result: ['Trieste', 'Trieste', 'Bologna', 'Bologna', 'Palermo']
```

### Step 4: Day Allocation

**Function**: `_allocate_days_to_route()`

**Simple counting**: Consecutive occurrences in route

```python
route = ['Trieste', 'Trieste', 'Bologna', 'Bologna', 'Palermo']
allocation = {'Trieste': 2, 'Bologna': 2, 'Palermo': 1}
```

### Step 5: Detailed Schedule Generation

**Function**: `_generate_detailed_schedule()`

**Running Clock System** (8:00 - 21:00):

```python
for day, city in enumerate(route):
    clock = 8.0  # Start at 8:00 AM
    
    # Add train travel time
    if moving_from_different_city:
        clock += train_travel_time
    
    # Knapsack POI selection
    pois = select_pois_until(clock, max_clock=21.0)
    # Each POI: 3 hours
    # Max POIs: (21 - clock) / 3
    
    # Track used POIs to avoid duplicates
    used_attractions[city].add(poi_name)
```

**POI Selection** (`_knapsack_attractions_with_clock`):
- Duration: 3 hours per POI
- Selection: Highest rated POIs that fit in available time
- Diversity: Uses curated 20 POIs with category balance

## Key Constraints

| Constraint | Value | Enforced At | Purpose |
|------------|-------|-------------|---------|
| `MAX_DAYS_PER_CITY` | 2 | DP transition | Force diverse routes |
| `MIN_STAY_HOURS` | 4 | DP transition | Ensure meaningful visits |
| `MAX_TRAIN_HOURS_PER_DAY` | 8 | DP transition | Realistic daily travel |
| `HOURS_PER_DAY` | 10 | Combined check | 8:00-21:00 window (13h - 3h meals) |
| `TRAIN_BUFFER_HOURS` | 1.0 | Travel time | Station access/waiting |
| `MAX_CANDIDATES` | 35 | Candidate selection | Performance optimization |
| `MAX_CONNECTIONS_PER_CITY` | 8 | Train matrix | Limit API calls |

## Scoring System

### City Score
```python
base_score = num_attractions * 10
interest_match = num_matching_categories * 15
total_score = base_score + interest_match + route_bonus
```

### DP Transition Scores

**STAY Transition**:
- `city_score * 0.7`: Reduced reward (encourage movement)
- `+ 30`: Stay bonus (saves travel)
- **Total**: ~100-150 for good cities

**MOVE Transition**:
- `city_score * 1.0`: Full city reward
- `+ 50`: Exploration bonus (visit new places)
- `- travel_time * 5`: Travel penalty
- **Total**: ~100-200 for nearby cities, ~50-100 for distant

**Balance**: MOVE generally preferred unless city is exceptional or travel is very long

## Example: Trieste → Palermo (5 days)

### Input
- Start: Trieste (northeast Italy)
- End: Palermo (Sicily)
- Days: 5
- Distance: ~1,500 km

### Execution

**Step 1 - Candidates** (top 35 from 106):
```
Bologna: detour=20km, route_bonus=198
Firenze: detour=40km, route_bonus=196
Roma: detour=60km, route_bonus=194
Napoli: detour=80km, route_bonus=192
Milano: detour=250km, route_bonus=175
Torino: detour=350km, route_bonus=165
```

**Step 2 - Train Matrix** (sample):
```
Day 1: Trieste → Bologna (4.0h, 9:00-13:00)
Day 2: Trieste → Bologna (4.0h, 13:00-17:00)
Day 3: Bologna → Roma (2.5h, 13:00-15:30)
Day 4: Roma → Napoli (1.5h, 13:00-14:30)
Day 5: Napoli → Palermo (ferry+train, 8h)
```

**Step 3 - DP Execution**:

| Day | State | Best Option | Score |
|-----|-------|-------------|-------|
| 1 | Trieste | Initialize | 120 |
| 2 | Trieste | STAY (day 1→2) | 204 (120+84) |
| 2 | Bologna | MOVE (1→2) | 190 (blocked: no day 1→2 train at 13:00) |
| 3 | Trieste | STAY (blocked: already 2 days) | - |
| 3 | Bologna | MOVE (2→3) | 360 (204+156) |
| 4 | Bologna | STAY (3→4) | 450 |
| 4 | Roma | MOVE (3→4) | 485 (360+125) |
| 5 | Roma | STAY (blocked: need Palermo) | - |
| 5 | Palermo | MOVE (4→5) | 580 (485+95) |

**Route**: `['Trieste', 'Trieste', 'Bologna', 'Roma', 'Palermo']`

**Step 4 - Allocation**:
```python
{'Trieste': 2, 'Bologna': 1, 'Roma': 1, 'Palermo': 1}
```

**Step 5 - Schedule**:
```
Day 1: Trieste (no train)
  8:00 - Clock start
  8:00-11:00: Grotta Gigante (3h, €10)
  11:00-14:00: Castello di Miramare (3h, €8)
  14:00-17:00: Piazza Unità d'Italia (3h, free)
  Cost: €18

Day 2: Trieste (from: Trieste)
  8:00 - Clock start
  8:00-11:00: Riserva Orsario (3h, €8)
  11:00-14:00: Teatro Romano (3h, €5)
  14:00-17:00: Faro della Vittoria (3h, free)
  Cost: €13

Day 3: Bologna (train 4.0h)
  8:00 + 4.0 = 12:00 - Clock after train
  12:00-15:00: Basilica San Petronio (3h, €5)
  15:00-18:00: Torri di Bologna (3h, €8)
  Cost: €13 + €35 (train)

Day 4: Roma (train 2.5h)
  8:00 + 2.5 = 10:30 - Clock after train
  10:30-13:30: Colosseo (3h, €16)
  13:30-16:30: Fontana di Trevi (3h, free)
  16:30-19:30: Piazza Navona (3h, free)
  Cost: €16 + €25 (train)

Day 5: Palermo (train 8.0h) [MAX limit]
  8:00 + 8.0 = 16:00 - Clock after train
  16:00-19:00: Catacombe Cappuccini (3h, €10)
  Cost: €10 + €80 (train+ferry)

Total: €210
```

## Performance Optimizations

### 1. Pre-calculated Distances
```python
# BEFORE: 106 cities × 2 distance calculations = 212 calls
# AFTER: 1 total_distance + 106 city calculations = 107 calls
total_distance = haversine(start, end)  # Once
for city in all_cities:
    detour = haversine(start, city) + haversine(city, end) - total_distance
```

### 2. Cached City Scores
```python
# Calculate once, reuse in DP
city_scores = {city: calculate_score(city) for city in candidates}
# Prevents O(days × candidates²) recalculations
```

### 3. Limited Search Space
- Candidates: 35 (not all 106)
- Connections per city: 8 (not all trains)
- Result: ~280 train queries per day instead of 11,130

### 4. Smart Train Search
- Day 1: 9:00 (realistic start)
- Day 2+: 13:00 (assume previous arrival)
- Avoids searching impossible early morning connections

## Edge Cases

### Case 1: No Valid Path
```python
# If DP can't reach end city:
if best_day == -1:
    # Fallback: stay at start, then direct to end
    route = [start] * (num_days - 1) + [end]
```

### Case 2: Short Route
```python
# If route < num_days:
# Padding removed (caused empty days bug)
# Now returns shorter route
```

### Case 3: No Trains Available
```python
# If no trains on specific day:
# DP skips that transition
# Alternative path found or fallback triggered
```

## Time Complexity

- **Candidate selection**: O(C log C) where C=106 cities
- **Train matrix**: O(D × N × K) where:
  - D = days
  - N = candidates (35)
  - K = connections per city (8)
  - ~1,400 train API calls for 5-day trip
- **DP**: O(D × N²) = O(5 × 35²) = ~6,000 operations
- **Total**: ~22-24 seconds for 5-day trip with cache

## Future Improvements

1. **Multi-objective optimization**: Pareto frontier for cost vs. attractions
2. **User preferences**: Weight exploration vs. stay based on traveler type
3. **Dynamic MAX_DAYS**: Adapt based on city size and attractions
4. **Beam search**: Explore top-K states per day instead of all
5. **A* integration**: Use heuristic to prune impossible paths early

---

**See also**: 
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) for performance analysis
- [RIEPILOGO_PROGETTO.md](RIEPILOGO_PROGETTO.md) for project overview
