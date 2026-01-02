# 🚂 Italian Train Trip Planner - Frontend

Modern web interface for the AI-powered Italian train trip planning system.

## 📁 Structure

```
frontend/
├── index.html          # Main web interface
├── styles.css          # Responsive CSS styling
├── app.js             # Frontend JavaScript logic
├── backend_server.py  # Minimal Flask backend bridge
└── README.md          # This file
```

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
# Make sure you're in the project root
cd /Users/tommasoaiello/Desktop/Magistrale/Software_Engineering/SEProejct

# Install Flask and CORS support
pip install flask flask-cors
```

### 2. Start the Backend Server

```bash
# From project root
python frontend/backend_server.py
```

The backend will start at `http://localhost:5000`

### 3. Open the Frontend

Open `frontend/index.html` in your browser:

```bash
# macOS
open frontend/index.html

# Or use Python's built-in server for better CORS handling
cd frontend
python -m http.server 8000
# Then visit: http://localhost:8000
```

## 🎨 Features

### User Interface
- **City Selection**: Visual grid with 10 major Italian cities
- **Interest Tags**: Art, History, Culture, Nature, Food, Architecture
- **Budget Planning**: Set your budget and see cost breakdowns
- **Date Selection**: Pick your start date for weather forecasts
- **Responsive Design**: Works on desktop, tablet, and mobile

### Trip Display
- **Daily Itinerary**: Detailed schedule with activities and timings
- **Weather Integration**: See weather forecasts and adapted recommendations
- **Cost Breakdown**: Activities, meals, accommodation separated
- **Travel Times**: Train journey durations between cities
- **Visual Timeline**: Beautiful cards showing each day's plan

## 🔌 API Endpoints

### POST `/api/plan`
Generate trip itinerary

**Request:**
```json
{
  "days": 4,
  "cities": ["Milano", "Bologna", "Firenze", "Roma"],
  "interests": ["arte", "storia", "cultura"],
  "budget": 500,
  "startDate": "2024-01-15",
  "useWeather": true
}
```

**Response:**
```json
{
  "days": [
    {
      "city": "Milano",
      "date": "2024-01-15",
      "activities": [...],
      "daily_cost": 120.50,
      "weather": {
        "condition": "Clear",
        "temp": 14
      }
    }
  ],
  "total_cost": 320.00,
  "weather_adapted": true,
  "within_budget": true
}
```

### GET `/api/cities`
List available cities

### GET `/api/health`
Health check

## 🛠️ Technology Stack

### Frontend
- **HTML5**: Semantic structure
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **Vanilla JavaScript**: No frameworks, pure ES6+
- **Responsive Design**: Mobile-first approach

### Backend Bridge
- **Flask**: Lightweight Python web framework
- **Flask-CORS**: Cross-Origin Resource Sharing support
- **Python 3.14**: Core backend integration

## 🎯 Usage Example

1. **Select Cities**: Click on Milano → Bologna → Firenze → Roma
2. **Set Duration**: 4 days
3. **Choose Interests**: Art, History, Culture
4. **Set Budget**: €500
5. **Pick Date**: Today or future date
6. **Generate**: Click "Generate Itinerary"
7. **View Results**: See complete daily schedule with costs

## 🔄 Data Flow

```
Frontend (HTML/CSS/JS)
    ↓ POST /api/plan
Backend Server (Flask)
    ↓ plan_trip()
ItineraryPlanner (Python)
    ↓ Uses:
    - CityDatabase (static + OSM)
    - TravelGraph (Dijkstra)
    - WeatherProvider (forecasts)
    ↓ Returns:
Formatted Itinerary
    ↓ JSON Response
Frontend Display (Cards/Timeline)
```

## 📱 Responsive Breakpoints

- **Desktop**: > 768px (full layout)
- **Tablet**: 768px - 480px (adapted grid)
- **Mobile**: < 480px (stacked layout)

## 🎨 Color Scheme

- **Primary**: #2563eb (Blue)
- **Secondary**: #10b981 (Green)
- **Warning**: #f59e0b (Amber)
- **Danger**: #ef4444 (Red)
- **Background**: Linear gradient (Purple tones)

## 🔧 Customization

### Adding New Cities

Edit `app.js`:
```javascript
const CITIES = [
    { name: 'NewCity', emoji: '🏰', region: 'Region' },
    // ...
];
```

### Changing Interests

Edit `index.html`:
```html
<label class="checkbox-label">
    <input type="checkbox" name="interests" value="new_interest">
    <span>🎭 New Interest</span>
</label>
```

## 🐛 Troubleshooting

### Backend not connecting
- Ensure Flask server is running: `python frontend/backend_server.py`
- Check console for CORS errors
- Verify port 5000 is not in use

### Cities not loading
- Check browser console for JavaScript errors
- Ensure `app.js` is loaded correctly
- Verify DOM is ready before initialization

### No results displaying
- Open browser DevTools Network tab
- Check API response status
- Verify backend can access `src/` modules

## 📝 TODO / Future Enhancements

- [ ] PDF export functionality
- [ ] Interactive map with route visualization
- [ ] Save/load itineraries (localStorage)
- [ ] Share itinerary via URL
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] Print-friendly view
- [ ] Mobile app (PWA)

## 🔗 Related Files

- **Backend System**: `src/itinerary_planner.py`
- **City Database**: `data/cities_database.json`
- **Demo Examples**: `examples/complete_demo.py`
- **Main Documentation**: `../README.md`

## 📄 License

Part of the Italian Train Trip Planner project.
