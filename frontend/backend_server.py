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

from dp_itinerary_planner import DPItineraryPlanner, TripInput

app = Flask(__name__)
# Enable CORS for frontend communication - allow all origins including file://
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize planner - nuovo DP planner con API treni reali
planner = DPItineraryPlanner()


def suggest_cities(start_city, num_days, interests, budget):
    """
    Suggest destination cities for round-trip mode
    Uses same selection logic as DP planner with proximity bias
    """
    # For smart_open mode (round trip), end city = start city
    # Let the DP planner determine the route
    return [start_city]  # DP planner will determine the full route


@app.route('/api/estimate-time', methods=['POST'])
def estimate_time():
    """
    Stima tempo di computazione prima di eseguire plan
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        
        duration = data.get('duration', 2)
        
        # Crea planner temporaneo per stima
        from dp_itinerary_planner import TripInput
        trip_input = TripInput(
            days=duration,
            start_city=data.get('start_city', 'Milano'),
            end_city=data.get('end_city', 'Roma'),
            interests=data.get('interests', ['arte']),
            start_date=datetime.now()
        )
        
        estimate = planner.estimate_computation_time(trip_input)
        
        return jsonify({
            'estimated_seconds': estimate['total_estimated'],
            'estimated_minutes': estimate['total_estimated'] / 60,
            'num_api_calls': estimate['num_api_calls'],
            'breakdown': {
                'candidate_selection': estimate['candidate_selection'],
                'train_matrix': estimate['train_matrix'],
                'optimization': estimate['dp_optimization'],
                'details': estimate['detail_generation']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        
        # Determine end city based on mode
        if mode == 'smart_open':
            # Round trip: start and return to same city
            # DP planner will determine optimal route
            end_city = start_city
            
        elif mode == 'smart_fixed':
            # DP trova route ottimale tra start e end
            if not end_city:
                return jsonify({'error': 'end_city required for smart_fixed mode'}), 400
            
            # Validate Sardinia isolation - cannot travel between island and mainland
            sardinian_cities = {'Cagliari', 'Sassari', 'Nuoro', 'Oristano'}
            start_in_sardinia = start_city in sardinian_cities
            end_in_sardinia = end_city in sardinian_cities
            
            if start_in_sardinia != end_in_sardinia:
                # One city in Sardinia, the other on mainland - impossible by train!
                return jsonify({
                    'error': 'Cannot plan train trip between Sardinia and mainland Italy',
                    'detail': f'{start_city} and {end_city} are not connected by train. Sardinia is an island with no rail connection to the mainland.',
                    'suggestion': 'Please choose both cities either in Sardinia or on the mainland.'
                }), 400
            
        elif mode == 'custom':
            # User fornisce lista città: usa prima e ultima come start/end
            cities = data.get('cities', [])
            if not cities or len(cities) < 2:
                return jsonify({'error': 'custom mode requires at least 2 cities'}), 400
            start_city = cities[0]
            end_city = cities[-1]
        else:
            return jsonify({'error': f'Invalid mode: {mode}'}), 400
        
        if not data.get('interests'):
            interests = ['arte', 'storia', 'cultura']
        
        # Parse start date
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        
        # Nuovo TripInput per DP planner (start+end, non più lista cities)
        trip_input = TripInput(
            days=duration,
            start_city=start_city,
            end_city=end_city,
            interests=interests,
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

        # Estrai route dall'itinerario generato dal DP
        route = []
        for day in itinerary_days:
            city = day.get('city')
            if city and city not in route:
                route.append(city)
        
        # Format response for frontend
        response = format_itinerary_for_frontend(itinerary_days, budget)
        response['mode'] = mode
        response['suggested_cities'] = route
        response['route'] = route
        response['total_days'] = duration
        response['itinerary'] = response.get('days', [])  # Aggiungi alias per compatibilità frontend
        
        print(f"   ✅ Success! {duration} days planned")
        return jsonify(response)
    
    except ValueError as e:
        print(f"   ❌ Validation error: {e}")
        return jsonify({"error": "Invalid start_date format. Expected YYYY-MM-DD"}), 400
    
    except HTTPException as e:
        return jsonify({"error": e.description}), e.code
    
    except Exception as e:
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
        # Debug: log train info
        if day.get('morning_train'):
            print(f"   🚂 Day {i+1} has train: {day.get('from_city')} → {day.get('city')}")
        
        formatted_day = {
            'day_number': i + 1,
            'city': day['city'],
            'date': day['date'].isoformat() if isinstance(day['date'], datetime) else day['date'],
            'available_hours': day.get('available_hours', 8),
            'travel_time': day.get('travel_time', 0),
            'from_city': day.get('from_city') or (days[i-1]['city'] if i > 0 else None),
            'morning_train': day.get('morning_train'),
            'pois': day.get('pois', []),
            'activities': [],
            'daily_cost': day.get('estimated_cost', 0) or day.get('daily_cost', 0),
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
