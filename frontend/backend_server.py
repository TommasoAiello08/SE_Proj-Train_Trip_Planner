"""
Minimal Flask Backend for Italian Train Trip Planner Frontend
Bridges the frontend with the core Python planning system
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sys
from pathlib import Path
from dataclasses import asdict, is_dataclass
from werkzeug.exceptions import HTTPException

# Add src directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from itinerary_planner import ItineraryPlanner, TripInput

app = Flask(__name__)
# Enable CORS for frontend communication - allow all origins including file://
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize planner
planner = ItineraryPlanner()


def suggest_cities(start_city, num_days, interests, budget):
    """
    Suggest destination cities based on starting point and preferences
    
    Strategy:
    - For 1-2 days: 2 cities (start + 1 nearby)
    - For 3-4 days: 3-4 cities (start + 2-3 destinations)
    - For 5+ days: 4-5 cities (start + 3-4 destinations)
    
    Selection criteria:
    - Geographic proximity (minimize travel time)
    - Interest matching (high score for user interests)
    - Variety (different regions/experiences)
    """
    from city_database import CityDatabase
    
    db = CityDatabase()
    start_city_data = db.get_city_by_name(start_city)
    
    if not start_city_data:
        # Fallback to popular cities
        return ['Milano', 'Firenze', 'Roma'][:min(num_days, 3)]
    
    # Use only cities from static DB to avoid OSM delays
    # Get all available cities directly from database
    all_city_names = [city['name'] for city in db.cities.values()]
    
    # Get all cities and calculate scores
    city_scores = []
    
    for city_name in all_city_names:
        if city_name == start_city:
            continue
            
        city_data = db.get_city_by_name(city_name)
        if not city_data:
            continue
        
        # Calculate score based on interests
        score = db.calculate_city_score(
            city=city_data,
            user_interests=interests,
            travel_time_hours=0  # For now, simplified
        )
        
        city_scores.append((city_name, score))
    
    # Sort by score (descending)
    city_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Determine number of destination cities
    if num_days <= 2:
        num_destinations = 1
    elif num_days <= 4:
        num_destinations = min(2, num_days - 1)
    else:
        num_destinations = min(4, num_days - 1)
    
    # Select top cities
    suggested = [start_city]
    suggested.extend([city for city, score in city_scores[:num_destinations]])
    
    return suggested


@app.route('/api/plan', methods=['POST'])
def plan_trip():
    """
    Flexible trip planning endpoint
    
    Modes:
    1. "smart_open": Start city only → AI suggests destinations
    2. "smart_fixed": Start + End city → AI suggests route between them
    3. "custom": User specifies all cities in order
    
    Expected JSON:
    {
        "mode": "smart_open" | "smart_fixed" | "custom",
        "start_city": str (required),
        "end_city": str (optional, for smart_fixed mode),
        "cities": list[str] (optional, for custom mode),
        "start_date": str (YYYY-MM-DD),
        "duration": int (days),
        "interests": list[str],
        "budget": float (optional, default 200/day)
    }
    """
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({
                "error": "JSON body required. Set Content-Type: application/json"
            }), 400
        print(f"\n🔍 Received request:")
        print(f"   Mode: {data.get('mode')}")
        print(f"   Start: {data.get('start_city')}")
        print(f"   End: {data.get('end_city')}")
        print(f"   Cities: {data.get('cities')}")
        print(f"   Duration: {data.get('duration')} days")
        
        mode = data.get('mode', 'smart_open')
        start_city = data.get('start_city')
        end_city = data.get('end_city')
        duration = data.get('duration', 2)
        interests = data.get('interests', ['arte', 'storia'])
        budget = data.get('budget', 200)
        
        # duration validation
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            return jsonify({"error": "duration must be an integer (days)"}), 400

        if duration < 1:
            return jsonify({"error": "duration must be >= 1"}), 400

        # optional: cap it so requests can't explode runtime
        if duration > 30:
            return jsonify({"error": "duration too large (max 30)"}), 400
        
        # Validate required fields
        missing = []

        if not start_city:
            missing.append("start_city")

        if not data.get("start_date"):
            missing.append("start_date")

        if mode == "smart_fixed" and not end_city:
            missing.append("end_city")

        if missing:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing
            }), 400
        
        # Determine cities based on mode
        if mode == 'smart_open':
            # AI suggests destinations from start city
            print(f"   → Smart Open: suggesting destinations from {start_city}")
            cities = suggest_cities(start_city, duration, interests, budget)
            
        elif mode == 'smart_fixed':
            # AI suggests route from start to end
            if not end_city:
                return jsonify({'error': 'end_city required for smart_fixed mode'}), 400
            print(f"   → Smart Fixed: route from {start_city} to {end_city}")
            cities = suggest_route_between(start_city, end_city, duration, interests, budget)
            
        elif mode == 'custom':
            # User provides all cities
            cities = data.get('cities', [])
            if not cities or len(cities) < 2:
                return jsonify({'error': 'custom mode requires at least 2 cities'}), 400
            print(f"   → Custom: user route {cities}")
        else:
            return jsonify({'error': f'Invalid mode: {mode}'}), 400
        
        print(f"   ✓ Final route: {cities}")
        print(f"   ✓ Final route: {cities}")
        
        if not data.get('interests'):
            interests = ['arte', 'storia', 'cultura']
        
        # Parse start date
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        
        trip_input = TripInput(
            days=duration,
            cities=cities,
            interests=interests,
            start_city=start_city,
            end_city=end_city,
            budget=budget,
            start_date=start_date
        )

        itinerary = planner.plan_trip(trip_input)
        
        print("DEBUG itinerary type:", type(itinerary))
        print("DEBUG itinerary repr:", repr(itinerary)[:500])
        
        from dataclasses import asdict, is_dataclass

        # Normalize itinerary to JSON-friendly structures
        if isinstance(itinerary, list):
            itinerary_days = [asdict(d) if is_dataclass(d) else d for d in itinerary]
        else:
            itinerary_days = itinerary  # fallback

        # Format response for frontend
        response = format_itinerary_for_frontend(itinerary_days, budget)
        response['mode'] = mode
        response['suggested_cities'] = cities
        response['route'] = cities
        
        print(f"   ✅ Success! {duration} days planned")
        return jsonify(response)
    
    except ValueError as e:
        print(f"   ❌ Validation error: {e}")
        return jsonify({"error": "Invalid start_date format. Expected YYYY-MM-DD"}), 400
    
    except HTTPException as e:
        return jsonify({"error": e.description}), e.code
    
    except Exception as e:
        print(f"   ❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def suggest_route_between(start_city, end_city, num_days, interests, budget):
    """
    Suggest intermediate cities between start and end
    """
    from city_database import CityDatabase
    
    db = CityDatabase()
    all_cities = list(db.cities.keys())
    
    # For short trips, just go direct
    if num_days <= 2:
        return [start_city, end_city]
    
    # For longer trips, add 1-2 interesting cities along the way
    # This is a simplified version - could use geographic routing
    intermediate = []
    for city_name in all_cities:
        if city_name in [start_city, end_city]:
            continue
        
        city = db.get_city(city_name)
        if not city:
            continue
        
        # Simple scoring based on interests
        score = 0
        city_interests = set(city.get('interests', []))
        user_interests = set(interests)
        score = len(city_interests & user_interests) * 10
        
        if score > 0:
            intermediate.append((city_name, score))
    
    intermediate.sort(key=lambda x: x[1], reverse=True)
    
    # Add 1-2 intermediate cities
    num_intermediate = min(num_days - 2, 2)
    route = [start_city]
    route.extend([city for city, _ in intermediate[:num_intermediate]])
    route.append(end_city)
    
    return route


def format_itinerary_for_frontend(itinerary, budget):
    """Convert backend itinerary format to frontend-friendly format"""
    
    formatted_days = []
    
    days = itinerary.get("days") if isinstance(itinerary, dict) else itinerary
    for i, day in enumerate(days):
        formatted_day = {
            'city': day['city'],
            'date': day['date'].isoformat() if isinstance(day['date'], datetime) else day['date'],
            'available_hours': day.get('available_hours', 8),
            'travel_time': day.get('travel_time', 0),
            'from_city': days[i-1]['city'] if i > 0 else None,
            'activities': [],
            'daily_cost': day.get('estimated_cost', 0),
            'weather': None
        }
        
        # Add weather info if available
        if 'weather' in day and day['weather']:
            formatted_day['weather'] = {
                'condition': day['weather'].get('description', 'Clear').title(),
                'temp': day['weather'].get('temp', 20)
            }
        
        # Format activities
        for activity in day.get('pois', []):
            formatted_activity = {
                'name': activity['name'],
                'start_time': activity.get('start_time', '09:00'),
                "duration": activity.get("duration_hours", activity.get("duration", 1)),
                "cost": activity.get("cost_euro", activity.get("cost", 0)),
                'rating': activity.get('rating', 8.0),
                'weather_adapted': day.get('weather_adapted', False),
                'indoor': activity.get('type', '').lower() in ['museum', 'gallery', 'church', 'indoor']
            }
            formatted_day['activities'].append(formatted_activity)
        
        formatted_days.append(formatted_day)
    
    # Calculate totals
    total_cost = sum(day['daily_cost'] for day in formatted_days)
    
    return {
        'days': formatted_days,
        'total_cost': total_cost,
        'weather_adapted': any(day.get('weather') for day in formatted_days),
        'within_budget': total_cost <= budget
    }


@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get list of available cities from database"""
    from city_database import CityDatabase
    
    db = CityDatabase()
    cities = []
    
    for city_id, city_data in db.cities.items():
        cities.append({
            'name': city_data['name'],
            'region': city_data.get('region', 'Unknown'),
            'lat': city_data['coordinates']['lat'],
            'lon': city_data['coordinates']['lon'],
            'has_station': city_data.get('station_code') is not None or city_data.get('has_train_station', False)
        })
    
    return jsonify(cities)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Italian Train Trip Planner API',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("🚂 Starting Italian Train Trip Planner Backend...")
    print("📍 API available at: http://localhost:5001")
    print("🌐 Frontend should connect to: http://localhost:5001/api/plan")
    print("\nEndpoints:")
    print("  POST /api/plan - Generate itinerary")
    print("  GET  /api/cities - List available cities")
    print("  GET  /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
