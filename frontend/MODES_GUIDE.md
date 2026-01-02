# 🎯 Planning Modes Guide

The Italian Train Trip Planner now supports **3 flexible planning modes** to accommodate different travel styles.

---

## 🚄 1. Quick Trip Mode

**Perfect for:** Day trips, business travel, short visits

### What It Does
Plan a same-day round trip from one city to another:
- Origin → Destination → Origin
- Automatically sets duration to 1 day
- Optimizes activities in destination city
- Returns you home the same evening

### How to Use
1. Select **"Quick Trip"** mode
2. Choose **Origin city** (where you start)
3. Choose **Destination city** (where you want to go)
4. Set interests and budget
5. Pick date for weather forecast
6. Generate!

### Example Use Cases
```
Milano → Venezia (1 day)
- Morning train to Venice
- Visit Piazza San Marco, Palazzo Ducale
- Afternoon gondola ride
- Evening train back to Milan

Roma → Firenze (1 day)
- Early train to Florence
- Uffizi Gallery, Duomo visit
- Lunch in Piazza della Signoria
- Return to Rome by evening
```

### Output
- Single day schedule
- Activities optimized for available time (minus travel)
- Train departure/arrival times
- Cost breakdown including round-trip estimate

---

## 🗺️ 2. Custom Route Mode

**Perfect for:** Travelers who know exactly where they want to go

### What It Does
Create multi-day itinerary with your pre-selected cities in your chosen order:
- Full control over route
- Select 2+ cities
- Order matters (route follows your selection)
- System allocates days proportionally

### How to Use
1. Select **"Custom Route"** mode
2. **Click cities in order** of visit (they get numbered)
3. Set **total duration** (days)
4. Choose interests and budget
5. Pick start date
6. Generate!

### Example Use Cases
```
Classic Grand Tour (4 days):
Milano → Bologna → Firenze → Roma
- Day 1: Milan
- Day 2: Bologna (after 2.5h train)
- Day 3: Florence (after 1.3h train)
- Day 4: Rome (after 2.8h train)

Northern Italy Circuit (6 days):
Venezia → Verona → Milano → Torino → Genova → Bologna
- 6 cities, balanced time allocation
- Geographic logic: minimize backtracking
```

### Features
- **Route Display**: Shows "City1 → City2 → City3" as you select
- **Order Badges**: Each city shows its number in the route
- **Deselection**: Click again to remove a city
- **Reordering**: Deselect and reselect to change order

### Output
- Multi-day schedule
- Day allocation based on city attractions
- Travel times between consecutive cities
- POI selection per city based on allocated time
- Total cost and budget status

---

## ✨ 3. Smart Planning Mode

**Perfect for:** Travelers who want expert suggestions

### What It Does
AI-powered destination recommendations based on:
- Your starting city
- Trip duration
- Your interests
- Your budget
- Geographic proximity
- Attraction quality

### How to Use
1. Select **"Smart Planning"** mode
2. Choose only your **starting city**
3. Set **trip duration**
4. Choose **interests** (critical for good suggestions!)
5. Set budget
6. Pick start date
7. Generate and see suggested route!

### Algorithm
```python
def suggest_cities(start, days, interests, budget):
    1. Calculate score for each potential destination
       - Interest matching (40%)
       - Attraction quality (30%)
       - Popularity (20%)
       - Distance from start (10%)
    
    2. Sort cities by score (highest first)
    
    3. Select top N cities where:
       - 1-2 days → 2 cities (start + 1)
       - 3-4 days → 3-4 cities (start + 2-3)
       - 5+ days → 4-5 cities (start + 3-4)
    
    4. Return: [start, city1, city2, ...]
```

### Example Use Cases
```
Starting from Milano, 4 days, interests: Art + History
Suggested Route: Milano → Venezia → Firenze → Roma
Reasoning:
- Venice: High art score, 2.5h from Milan
- Florence: Renaissance art capital
- Rome: Ancient history + art museums

Starting from Roma, 3 days, interests: Food + Nature
Suggested Route: Roma → Napoli → Bologna
Reasoning:
- Naples: Pizza capital, coastal beauty
- Bologna: Food paradise, gastronomic culture

Starting from Venezia, 2 days, interests: Architecture
Suggested Route: Venezia → Verona
Reasoning:
- Verona: Close proximity (1h), rich architecture
- Perfect for weekend trip
```

### Output
- **Suggestion Banner**: Shows recommended route
- **Explanation**: "Based on your interests and starting point"
- Full itinerary with suggested cities
- Same detailed schedule as Custom Route mode

---

## 📊 Mode Comparison

| Feature | Quick Trip | Custom Route | Smart Planning |
|---------|-----------|--------------|----------------|
| **Duration** | Fixed (1 day) | User choice (1-14) | User choice (1-14) |
| **Cities** | 2 (origin + dest) | 2+ (user selected) | 2+ (AI suggested) |
| **Control** | High | Full | Low (trust AI) |
| **Effort** | Minimal | Medium | Minimal |
| **Best For** | Day trips | Planned tours | Open exploration |
| **Flexibility** | Low | High | Medium |

---

## 🎨 Interest Impact by Mode

### Quick Trip
Interests affect:
- ✅ Activities in destination city
- ✅ POI selection priority
- ❌ Destination choice (you decide)

### Custom Route
Interests affect:
- ✅ POI selection in each city
- ✅ Activity types per day
- ✅ Indoor/outdoor balance with weather
- ❌ City selection (you decide)
- ❌ Route order (you decide)

### Smart Planning
Interests affect:
- ✅ **City destination selection** (40% weight!)
- ✅ POI selection in each city
- ✅ Route optimization
- ✅ Activity types per day
- ✅ Indoor/outdoor balance

**Example:**
```
Start: Milano, 4 days, €500

Interests: Art + History
→ Milano → Venezia → Firenze → Roma
  (Classic cultural cities)

Interests: Food + Nature
→ Milano → Torino → Bologna → Genova
  (Gastronomic + Alpine/Coastal)

Interests: Architecture + Culture
→ Milano → Verona → Venezia → Padova
  (Architectural gems + cultural centers)
```

---

## 🔄 Switching Between Modes

You can switch modes at any time before generating:

1. **Quick → Custom**: Need more than 1 day
2. **Quick → Smart**: Want suggestions instead of fixed destination
3. **Custom → Quick**: Realized 1 day is enough
4. **Custom → Smart**: Too many options, want AI help
5. **Smart → Custom**: Disagree with suggestions, want control
6. **Smart → Quick**: Suggested route too complex

**UI Updates Automatically:**
- Input fields change based on mode
- Validation rules adjust
- Duration field shows/hides/locks
- City selection UI changes (dropdown vs grid)

---

## 💡 Tips & Best Practices

### Quick Trip
- ✅ Choose nearby cities (< 2.5 hours)
- ✅ Select 3-5 interests for variety
- ✅ Budget: €100-150 per person
- ❌ Don't pick cities 5+ hours apart

### Custom Route
- ✅ Plan geographic logic (north→south)
- ✅ Mix large/small cities for variety
- ✅ Allow 1-2 days per major city
- ❌ Don't backtrack unnecessarily
- ❌ Don't overcrowd (max 6 cities/week)

### Smart Planning
- ✅ Select **specific interests** (not all!)
- ✅ Trust the algorithm initially
- ✅ Try different starting cities
- ✅ Adjust budget if suggestions seem off
- ❌ Don't select 6 interests (too generic)
- ❌ Don't expect exact match if unrealistic

---

## 🧪 Testing Scenarios

### Scenario 1: Business Day Trip
```
Mode: Quick Trip
Origin: Milano
Destination: Roma
Interests: Culture, Architecture
Budget: €200
Expected: Morning train, 2-3 major sites, evening return
```

### Scenario 2: Planned Tour
```
Mode: Custom Route
Cities: Firenze → Siena → Perugia → Roma (4 days)
Interests: History, Art
Budget: €600
Expected: Hidden gems tour with OSM cities
```

### Scenario 3: Open Exploration
```
Mode: Smart Planning
Start: Venezia
Duration: 5 days
Interests: Nature, Food
Budget: €700
Expected: Coastal/Alpine route with culinary focus
```

---

## 🐛 Troubleshooting

### "Please select both origin and destination"
- **Mode:** Quick Trip
- **Fix:** Choose cities in both dropdowns

### "Please select at least 2 cities"
- **Mode:** Custom Route
- **Fix:** Click at least 2 city cards

### "Please select a starting city"
- **Mode:** Smart Planning
- **Fix:** Choose city in dropdown

### Cities suggested don't match interests
- **Mode:** Smart Planning
- **Fix:** 
  1. Reduce number of selected interests (2-3 max)
  2. Check if interests are compatible
  3. Try different starting city
  4. Increase budget (affects feasibility)

### Quick Trip shows "No activities"
- **Cause:** Cities too far apart
- **Fix:** Choose closer cities (< 3 hours)

---

## 🚀 Future Enhancements

Potential additions to modes:

**Quick Trip:**
- [ ] Multi-stop day trip (A→B→C→A)
- [ ] Half-day option
- [ ] Late night return option

**Custom Route:**
- [ ] Drag-and-drop reordering
- [ ] Route optimization (TSP)
- [ ] Alternative route suggestions

**Smart Planning:**
- [ ] Budget-based suggestions (cheap vs luxury)
- [ ] Seasonal recommendations
- [ ] Crowd-avoidance mode
- [ ] Instagram-worthy route

---

**Enjoy the flexibility! 🎉**

Choose the mode that fits your travel style and let the system do the rest.
