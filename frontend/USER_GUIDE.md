# 🚂 Italian Train Trip Planner - User Guide

Complete guide to using the Italian Train Trip Planner web application.

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Planning Your Trip](#planning-your-trip)
3. [Understanding Results](#understanding-results)
4. [Tips & Best Practices](#tips--best-practices)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### Option 1: Quick Start (Recommended)

```bash
cd /Users/tommasoaiello/Desktop/Magistrale/Software_Engineering/SEProejct
./start.sh
```

This will:
- Start the backend server
- Open the frontend in your browser
- Display connection information

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
python frontend/backend_server.py
```

**Terminal 2 - Frontend:**
```bash
open frontend/index.html
```

### Verify Everything Works

1. Check backend health: Visit [http://localhost:5001/api/health](http://localhost:5001/api/health)
2. You should see: `{"status": "healthy", ...}`

---

## 🗺️ Planning Your Trip

### Step 1: Select Cities

Click on the cities you want to visit **in the order you want to visit them**:

- **First click**: City #1 (your starting point)
- **Second click**: City #2 (first destination)
- **Third click**: City #3 (second destination)
- And so on...

**Available Cities:**
- 🏢 Milano (Lombardia) - Fashion & Business
- 🏛️ Roma (Lazio) - Ancient History
- 🎨 Firenze (Toscana) - Renaissance Art
- 🛶 Venezia (Veneto) - Romantic Canals
- 🌋 Napoli (Campania) - Pizza & Coast
- ⛰️ Torino (Piemonte) - Royal Palaces
- 🍝 Bologna (Emilia-Romagna) - Food Capital
- 💕 Verona (Veneto) - Romeo & Juliet
- ⚓ Genova (Liguria) - Maritime History
- 🗼 Pisa (Toscana) - Leaning Tower

**Tips:**
- Start with a major city (Milano, Roma, Firenze)
- Consider geographic proximity to minimize travel time
- The route will be: City1 → City2 → City3 → ...

### Step 2: Set Duration

Enter the total number of days for your trip (1-14 days).

**Recommendations:**
- **2-3 days**: 2-3 cities (Venice → Verona)
- **4-6 days**: 3-4 cities (Milan → Bologna → Florence → Rome)
- **7-10 days**: 4-6 cities (Grand Tour)
- **10+ days**: 6+ cities (Comprehensive Italy)

**Note:** The system automatically allocates days to cities based on:
- Number of attractions available
- Average attraction ratings
- Travel time between cities

### Step 3: Choose Interests

Select one or more interests that match your preferences:

- 🎨 **Art**: Museums, galleries, Renaissance masterpieces
- 🏺 **History**: Ancient ruins, historical sites, monuments
- 📚 **Culture**: Cultural centers, traditions, local experiences
- 🌳 **Nature**: Parks, gardens, natural landscapes
- 🍕 **Food**: Culinary experiences, local cuisine
- 🏛️ **Architecture**: Churches, palaces, architectural wonders

**How It Works:**
The system scores attractions based on your interests. For example:
- If you select "Art", the Uffizi Gallery in Florence gets a higher score
- If you select "History", the Colosseum in Rome is prioritized
- Multiple interests = broader range of activities

### Step 4: Set Budget

Enter your **total budget per person** in euros (€).

**Budget Includes:**
- 🎭 Attraction entrance fees
- 🍽️ Meals (€30/day)
- 🏨 Accommodation estimates
- ❌ NOT included: train tickets, shopping, extras

**Budget Guidelines:**
- **€200-300**: Budget trip, 2-3 days, basic accommodations
- **€400-600**: Moderate trip, 4-5 days, mid-range hotels
- **€700-1000**: Comfortable trip, 6-8 days, quality hotels
- **€1000+**: Luxury trip, 10+ days, premium experiences

**Note:** If you exceed your budget, the system will still generate the itinerary but show a warning.

### Step 5: Choose Start Date

Select the date you plan to start your trip.

**Weather Integration:**
- Dates within next 5 days: Real weather forecasts
- Dates beyond 5 days: Historical averages
- Weather affects POI recommendations (indoor/outdoor)

### Step 6: Weather Toggle

Keep **"Use weather forecast for POI selection"** checked to:
- Get indoor activities on rainy days
- Get outdoor activities on sunny days
- Optimize your experience based on conditions

**How It Works:**
- ☀️ **Sunny + Outdoor**: +2 score bonus (parks, piazzas)
- 🌧️ **Rainy + Indoor**: +3 score bonus (museums, galleries)
- 🌧️ **Rainy + Outdoor**: -2 score penalty (avoid outdoor sites)
- ☀️ **Sunny + Indoor**: -1 score penalty (don't waste sunshine)

### Step 7: Generate!

Click **"🚀 Generate Itinerary"** and wait 5-60 seconds:
- **5-15 seconds**: Cities in database (Milano, Roma, etc.)
- **30-60 seconds**: Cities not in database (uses OpenStreetMap)

---

## 📊 Understanding Results

### Trip Summary

The top section shows:

| Metric | Description |
|--------|-------------|
| **Days** | Total trip duration |
| **Cities** | Number of cities visited |
| **Attractions** | Total POIs/activities |
| **Travel Time** | Total hours on trains |
| **Total Cost** | All expenses (activities + meals + accommodation) |
| **Weather Adapted** | Whether weather was considered |

### Daily Schedule

Each day card shows:

**Header:**
- Day number and city name
- Date and available hours
- Weather forecast (temperature and condition)

**Travel Info (if applicable):**
- Train journey duration from previous city

**Activities:**
Each activity shows:
- **Time**: Start time (e.g., 09:00)
- **Name**: Attraction name
- **Duration**: How long to spend (hours)
- **Cost**: Entrance fee (€)
- **Rating**: Quality score (0-10)
- **Type**: Indoor/Outdoor badge (if weather-adapted)

**Daily Cost:**
- Activities total
- Meals (fixed €30)
- Accommodation estimate

### Cost Breakdown

**Detailed Breakdown:**
- 🎭 Attractions & Activities
- 🍽️ Meals (€30/day)
- 🏨 Accommodation

**Budget Status:**
- ✅ Green = Within budget (shows remaining)
- ⚠️ Yellow = Over budget (shows excess)

---

## 💡 Tips & Best Practices

### Planning Tips

1. **Start Big**: Begin in major cities (Milan, Rome, Florence) with better train connections
2. **Go Geographic**: Plan routes that make geographic sense (North→South or vice versa)
3. **Time Management**: Allow 6-8 hours per city for sightseeing (after travel)
4. **Buffer Days**: Consider rest days for longer trips (not currently in system)

### Budget Tips

1. **Museum Days**: Major museums cost €15-20 each
2. **Free Options**: Many churches and piazzas are free
3. **Food Budget**: €30/day covers 3 modest meals
4. **Accommodation**: €60-100/night for mid-range hotels

### Interest Selection

1. **Be Specific**: Select only your true interests for better recommendations
2. **Mix & Match**: Combine interests (Art + Food) for balanced itineraries
3. **Weather Synergy**: Culture/Art works great with weather adaptation (museums on rainy days)

### Route Examples

**Classic Grand Tour** (4 days):
```
Milano → Bologna → Firenze → Roma
Interests: Art, History, Culture
Budget: €500
```

**Hidden Gems** (3 days):
```
Firenze → Siena → Perugia
Interests: History, Nature, Food
Budget: €400
```

**Romantic Weekend** (2 days):
```
Venezia → Verona
Interests: Culture, Architecture
Budget: €300
```

**Comprehensive North** (6 days):
```
Milano → Torino → Genova → Bologna → Venezia → Verona
Interests: All
Budget: €800
```

---

## 🔧 Troubleshooting

### Backend Not Connecting

**Problem:** "Server error" or "Failed to fetch"

**Solutions:**
1. Check backend is running:
   ```bash
   curl http://localhost:5001/api/health
   ```
2. Restart backend:
   ```bash
   ./start.sh
   ```
3. Check port availability:
   ```bash
   lsof -i :5001
   ```

### No Results Displayed

**Problem:** Loading spinner never stops

**Solutions:**
1. Open browser console (F12 → Console tab)
2. Look for red errors
3. Check network tab for failed requests
4. Verify you selected at least 2 cities

### Slow Generation

**Problem:** Takes more than 60 seconds

**Reasons:**
- First time using OSM for a city (fetching 50+ POIs)
- Weather API rate limiting
- Complex itinerary (many cities/days)

**Normal:**
- 5-15 seconds for cached cities
- 30-60 seconds for OSM cities

### Budget Always Exceeded

**Problem:** Cost always over budget

**Solutions:**
1. Increase budget (system estimates €80-100/day minimum)
2. Reduce trip duration
3. Select fewer expensive cities (avoid Rome, Venice)
4. System prioritizes quality over budget adherence

### Weather Not Showing

**Problem:** No weather icons or "Weather Adapted: No"

**Reasons:**
1. Start date more than 5 days away (demo mode)
2. Weather API quota exceeded (unlikely)
3. Weather checkbox unchecked

**Note:** Demo mode still adapts POIs using historical data

---

## 📞 Support & Feedback

### Check Logs

Backend logs show:
```
✅ Database loaded: 10 cities
✅ Grafo caricato da cache: 10 città
🌤️ Weather provider initialized (Demo mode)
```

### Common Warnings

```
⚠️ Weather forecast not available for [date]
→ Normal for dates beyond 5 days
```

```
⚠️ City [name] not in database, using OSM
→ Normal for non-major cities, takes longer
```

```
⚠️ No train connections found for [city]
→ City not reachable by train, use haversine estimate
```

### Report Issues

If you encounter bugs:
1. Note the exact input (cities, days, interests, budget)
2. Check browser console for errors
3. Check backend terminal output
4. Try with different inputs to isolate issue

---

## 🎯 Example Session

**Scenario:** 4-day art & culture tour with €500 budget

1. **Select Cities:** Milano → Bologna → Firenze → Roma
2. **Duration:** 4 days
3. **Interests:** ✓ Art, ✓ History, ✓ Culture
4. **Budget:** €500
5. **Start Date:** Today
6. **Weather:** ✓ Enabled
7. **Click:** Generate Itinerary

**Expected Result:**
- Day 1: Milan (4 attractions: Duomo, Galleria, Castello, Santa Maria)
- Day 2: Bologna (3 attractions after 2.5h train)
- Day 3: Florence (2 attractions after 1.3h train: Uffizi, Duomo)
- Day 4: Rome (2 attractions after 2.8h train: Colosseo, Fontana)
- **Total:** 11 POIs, 6.6h travel, €320 (✅ Under budget!)

---

**Enjoy planning your perfect Italian journey! 🇮🇹✨**
