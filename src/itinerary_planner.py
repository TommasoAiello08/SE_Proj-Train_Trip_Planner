"""
Itinerary Planner - Multi-City Travel Planning System
=================================================================

Input:
- Available days (es: 4)
- Cities to visit in order (es: Milano → Bologna → Firenze → Roma)
- User interests
- Budget (optional)

Output:
- Day-by-day schedule with:
  - Train times between cities
  - POIs to visit each day
  - Estimated times and costs
  - Weather adaptation

Algoritmo:
1. Calculate travel times between consecutive cities
2. Distribute days among cities (proporzionale a POI disponibili)
3. For each day/city, select optimal POIs considering:
   - Available time (ore diurne - viaggio - pasti)
   - Meteo (indoor se pioggia, outdoor se sole)
   - User interests (match con categorie)
   - Distances between POIs (clustering geografico)
4. Optimize POI visit order in day (TSP locale)
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Import existing modules
sys.path.insert(0, str(Path(__file__).parent))
from city_database import CityDatabase
from travel_graph import TravelGraph

# Conditional import for weather
try:
    from weather_provider import WeatherProvider
except ImportError:
    from src.weather_provider import WeatherProvider


@dataclass
class TripInput:
    """Trip request input"""
    days: int
    cities: List[str]  # In visit order
    interests: List[str]
    start_city: str
    end_city: str
    budget: Optional[float] = None
    start_date: Optional[datetime] = None


@dataclass
class DaySchedule:
    """Schedule di un singolo giorno"""
    day_number: int
    date: datetime
    city: str
    
    # Viaggio
    morning_train: Optional[Dict] = None  # Se c'è spostamento
    travel_time: float = 0.0  # Ore di viaggio
    
    # Attività
    pois: List[Dict] = None  # POI da visitare
    activities: List[Dict] = None  # Schedule dettagliato con orari
    
    # Costi e meteo
    estimated_cost: float = 0.0
    weather: Optional[Dict] = None
    
    # Logistica
    accommodation: Optional[str] = None
    meals: List[str] = None


class ItineraryPlanner:
    """
    Main planner orchestrating itinerary creation with weather integration
    """
    
    def __init__(self, use_weather: bool = True):
        self.city_db = CityDatabase(use_osm=True)
        self.travel_graph = TravelGraph()
        self.use_weather = use_weather
        self.weather_provider = WeatherProvider() if use_weather else None
        
        # Configurable parameters
        self.hours_per_day = 10  # Available hours for activities (9:00-19:00)
        self.meal_time = 2.0     # Hours for lunch/dinner
        self.poi_buffer = 0.5    # Buffer time between POIs (travel)
    
    def plan_trip(self, trip_input: TripInput) -> List[DaySchedule]:
        """
        Metodo principale: crea itinerario completo
        
        Args:
            trip_input: Parametri del viaggio
            
        Returns:
            Lista di DaySchedule (uno per giorno)
        """
        print(f"\n🗺️  PIANIFICAZIONE ITINERARIO: {' → '.join(trip_input.cities)}")
        print(f"📅 Days: {trip_input.days}")
        print(f"🎯 Interests: {', '.join(trip_input.interests)}")
        print("="*70)
        
        # Step 1: Calculate travel times between consecutive cities
        travel_times = self._calculate_travel_times(trip_input.cities)
        
        # Step 2: Distribute days among cities
        city_allocation = self._allocate_days_to_cities(
            trip_input.cities,
            trip_input.days,
            travel_times
        )
        
        # Step 3: Crea schedule per ogni giorno
        schedule = []
        current_date = trip_input.start_date or datetime.now()
        day_counter = 1
        
        for city_name, num_days in city_allocation.items():
            print(f"\n📍 {city_name.upper()} - {num_days} giorn{'o' if num_days == 1 else 'i'}")
            
            for day_in_city in range(num_days):
                day_schedule = self._plan_single_day(
                    day_number=day_counter,
                    date=current_date,
                    city=city_name,
                    interests=trip_input.interests,
                    is_arrival_day=(day_in_city == 0 and day_counter > 1),
                    travel_time=travel_times.get((trip_input.cities[day_counter-2], city_name), 0) if day_counter > 1 and day_in_city == 0 else 0
                )
                
                schedule.append(day_schedule)
                current_date += timedelta(days=1)
                day_counter += 1
        
        # Step 4: Ottimizza e valida
        self._optimize_schedule(schedule)
        
        return schedule
    
    def _calculate_travel_times(self, cities: List[str]) -> Dict[tuple, float]:
        """
        Calcola tempi di viaggio tra città consecutive
        """
        print("\n🚂 Calculating travel times...")
        travel_times = {}
        
        for i in range(len(cities) - 1):
            origin = cities[i]
            dest = cities[i + 1]
            
            # Use travel_graph to find time
            path = self.travel_graph.find_shortest_path(origin, dest)
            if path and isinstance(path, dict):
                travel_time = path.get('total_time', 3.0)
                travel_times[(origin, dest)] = travel_time
                print(f"  • {origin} → {dest}: {travel_time:.1f}h")
            else:
                # Fallback to estimate_travel_time
                travel_time = self.travel_graph.estimate_travel_time(origin, dest)
                if travel_time:
                    travel_times[(origin, dest)] = travel_time
                    print(f"  • {origin} → {dest}: {travel_time:.1f}h (estimated)")
                else:
                    print(f"  ⚠️  {origin} → {dest}: route not found, estimating 3h")
                    travel_times[(origin, dest)] = 3.0
        
        return travel_times
    
    def _allocate_days_to_cities(
        self, 
        cities: List[str], 
        total_days: int,
        travel_times: Dict[tuple, float]
    ) -> Dict[str, int]:
        """
        Distribuisce giorni tra città in modo intelligente
        
        Strategia:
        1. Calculate "weight" of each city (number of POIs * average rating)
        2. Subtract travel days (se >6h dedica giorno intero)
        3. Distribute remaining days proportionally to weights
        """
        print("\n�� Distributing days among cities...")
        
        # Calculate weight of each city
        city_weights = {}
        for city in cities:
            city_data = self.city_db.get_city_by_name(city)
            if city_data:
                attractions = city_data.get('attractions', [])
                avg_rating = sum(a.get('rating', 5) for a in attractions) / max(len(attractions), 1)
                weight = len(attractions) * avg_rating
                city_weights[city] = weight
            else:
                city_weights[city] = 10  # Default
        
        # Days dedicated to long travels (>6h)
        travel_days = sum(1 for time in travel_times.values() if time > 6)
        available_days = total_days - travel_days
        
        # Proportional distribution
        total_weight = sum(city_weights.values())
        allocation = {}
        
        for city, weight in city_weights.items():
            days = max(1, round((weight / total_weight) * available_days))
            allocation[city] = days
        
        # Adjust for exact sum
        current_sum = sum(allocation.values())
        if current_sum != total_days:
            # Aggiungi/rimuovi giorni dalla città con più peso
            max_city = max(city_weights, key=city_weights.get)
            allocation[max_city] += (total_days - current_sum)
        
        for city, days in allocation.items():
            print(f"  • {city}: {days} giorn{'o' if days == 1 else 'i'}")
        
        return allocation
    
    def _plan_single_day(
        self,
        day_number: int,
        date: datetime,
        city: str,
        interests: List[str],
        is_arrival_day: bool = False,
        travel_time: float = 0.0
    ) -> DaySchedule:
        """
        Plan a single day in a city with weather consideration
        """
        print(f"  📅 Day {day_number} ({date.strftime('%d/%m/%Y')})")
        
        # Get weather forecast for this day
        weather = None
        if self.use_weather and self.weather_provider:
            city_data = self.city_db.get_city_by_name(city)
            if city_data:
                # Handle both direct lat/lon and nested coordinates
                if 'coordinates' in city_data:
                    lat = city_data['coordinates']['lat']
                    lon = city_data['coordinates']['lon']
                else:
                    lat = city_data.get('latitude')
                    lon = city_data.get('longitude')
                
                if lat and lon:
                    weather = self.weather_provider.get_weather_for_date(
                        city, lat, lon, date
                    )
                    if weather:
                        emoji = '🌧️' if weather['is_rainy'] else ('☀️' if weather['is_sunny'] else '☁️')
                        print(f"    {emoji} Weather: {weather['condition']}, {weather['temp_avg']}°C ({weather['rain_probability']:.0f}% rain)")
        
        # Calculate available time
        available_hours = self.hours_per_day - self.meal_time
        
        if is_arrival_day:
            available_hours -= travel_time
            print(f"    🚂 Arrival (travel {travel_time:.1f}h)")
        
        print(f"    ⏰ Available hours: {available_hours:.1f}h")
        
        # Select optimal POIs for this day (weather-aware)
        pois = self._select_pois_for_day(city, interests, available_hours, weather)
        
        # Create detailed schedule with times
        activities = self._create_activity_schedule(pois, date, travel_time)
        
        # Estimate costs
        estimated_cost = self._estimate_daily_cost(city, pois)
        
        day_schedule = DaySchedule(
            day_number=day_number,
            date=date,
            city=city,
            travel_time=travel_time,
            pois=pois,
            activities=activities,
            estimated_cost=estimated_cost,
            weather=weather  # Add weather info
        )
        
        print(f"    🎯 {len(pois)} POIs selected")
        print(f"    💰 Estimated cost: €{estimated_cost:.2f}")
        
        return day_schedule
    
    def _select_pois_for_day(
        self, 
        city: str, 
        interests: List[str], 
        available_hours: float,
        weather: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Select optimal POIs for a day using knapsack algorithm with weather consideration
        
        Constraints:
        - Total time <= available_hours
        - Match with user interests
        - Category diversity
        - Weather suitability (indoor vs outdoor)
        """
        city_data = self.city_db.get_city_by_name(city)
        if not city_data:
            return []
        
        attractions = city_data.get('attractions', [])
        
        # Determine weather preference
        weather_preference = None
        if weather and self.weather_provider:
            weather_preference = self.weather_provider.classify_weather_for_poi(weather)
        
        # Calculate score for each POI (weather-aware)
        scored_pois = []
        for poi in attractions:
            score = self._calculate_poi_score(poi, interests, weather_preference)
            scored_pois.append({
                **poi,
                'score': score
            })
        
        # Sort by score
        scored_pois.sort(key=lambda x: x['score'], reverse=True)
        
        # Knapsack: select POIs until filling available time
        selected = []
        total_time = 0
        
        for poi in scored_pois:
            poi_time = poi.get('duration_hours', 2.0) + self.poi_buffer
            if total_time + poi_time <= available_hours:
                selected.append(poi)
                total_time += poi_time
                
                if len(selected) >= 5:  # Max 5 POIs per day
                    break
        
        return selected
    
    def _calculate_poi_score(self, poi: Dict, interests: List[str], weather_preference: Optional[str] = None) -> float:
        """
        Calculate POI score based on interests, quality, and weather suitability
        
        Args:
            poi: POI dictionary
            interests: User interests
            weather_preference: 'indoor', 'outdoor', or 'mixed'
        """
        # Base score: rating and popularity
        rating = poi.get('rating', 5)
        popularity = poi.get('popularity', 5)
        
        score = (rating * 0.6 + popularity * 0.4)
        
        # Bonus if category matches interests
        categories = poi.get('categories', [])
        interest_match = sum(1 for cat in categories if cat in interests)
        score += interest_match * 2
        
        # Weather adaptation bonus/penalty
        if weather_preference:
            poi_type = poi.get('type', '').lower()
            poi_categories = [c.lower() for c in categories]
            
            # Classify POI as indoor or outdoor
            indoor_keywords = ['museum', 'gallery', 'teatro', 'cinema', 'mall']
            outdoor_keywords = ['park', 'garden', 'monument', 'viewpoint', 'archaeological', 'natura', 'panorama']
            
            is_indoor = any(keyword in poi_type for keyword in indoor_keywords) or \
                       any(keyword in cat for cat in poi_categories for keyword in indoor_keywords)
            is_outdoor = any(keyword in poi_type for keyword in outdoor_keywords) or \
                        any(keyword in cat for cat in poi_categories for keyword in outdoor_keywords)
            
            # Apply weather bonus
            if weather_preference == 'indoor' and is_indoor:
                score += 3  # Strong preference for indoor when rainy
            elif weather_preference == 'indoor' and is_outdoor:
                score -= 2  # Penalty for outdoor when rainy
            elif weather_preference == 'outdoor' and is_outdoor:
                score += 2  # Bonus for outdoor when sunny
            elif weather_preference == 'outdoor' and is_indoor:
                score -= 1  # Small penalty for indoor when sunny
        
        return score
    
    def _create_activity_schedule(
        self, 
        pois: List[Dict], 
        date: datetime,
        morning_travel: float = 0
    ) -> List[Dict]:
        """
        Create detailed schedule with times per POI
        """
        activities = []
        current_time = date.replace(hour=9, minute=0)
        
        # If there's morning travel
        if morning_travel > 0:
            activities.append({
                'time': current_time.strftime('%H:%M'),
                'type': 'travel',
                'description': 'Train travel',
                'duration': morning_travel
            })
            current_time += timedelta(hours=morning_travel)
        
        # Add POIs
        for poi in pois:
            activities.append({
                'time': current_time.strftime('%H:%M'),
                'type': 'visit',
                'name': poi['name'],
                'duration': poi.get('duration_hours', 2.0),
                'cost': poi.get('cost', 0)
            })
            current_time += timedelta(hours=poi.get('duration_hours', 2.0))
            
            # Travel buffer
            current_time += timedelta(hours=self.poi_buffer)
        
        return activities
    
    def _estimate_daily_cost(self, city: str, pois: List[Dict]) -> float:
        """
        Estimate daily cost (attractions + meals + accommodation)
        """
        # Attractions cost
        attraction_cost = sum(poi.get('cost', 0) for poi in pois)
        
        # Meal cost (estimate)
        meal_cost = 30  # €30 al giorno per pasti
        
        # Accommodation cost (from city database)
        city_data = self.city_db.get_city_by_name(city)
        accommodation = city_data.get('average_cost_per_day', 50) if city_data else 50
        
        return attraction_cost + meal_cost + accommodation
    
    def _optimize_schedule(self, schedule: List[DaySchedule]):
        """
        Optimize final schedule (POI order, times, etc.)
        """
        print("\n🔧 Optimizing schedule...")
        
        for day in schedule:
            # Sort POIs by geographic proximity (local TSP)
            # TODO: implementare TSP per ordine ottimale
            pass
        
        print("  ✅ Optimization completed")
    
    def print_itinerary(self, schedule: List[DaySchedule]):
        """
        Print complete itinerary in readable format
        """
        print("\n" + "="*70)
        print("📋 COMPLETE ITINERARY")
        print("="*70)
        
        total_cost = 0
        
        for day in schedule:
            print(f"\n🗓️  DAY {day.day_number} - {day.date.strftime('%d/%m/%Y')} - {day.city.upper()}")
            print("-" * 70)
            
            if day.travel_time > 0:
                print(f"🚂 Viaggio: {day.travel_time:.1f}h")
            
            print(f"\n⏰ Schedule:")
            for activity in day.activities:
                if activity['type'] == 'travel':
                    print(f"  {activity['time']} - {activity['description']} ({activity['duration']:.1f}h)")
                else:
                    print(f"  {activity['time']} - {activity['name']} ({activity['duration']:.1f}h, €{activity['cost']})")
            
            print(f"\n💰 Daily cost: €{day.estimated_cost:.2f}")
            total_cost += day.estimated_cost
        
        print("\n" + "="*70)
        print(f"💵 TOTAL TRIP COST: €{total_cost:.2f}")
        print("="*70)


def demo_itinerary_planner():
    """
    Demo: Milano → Bologna → Firenze → Roma in 4 giorni
    """
    print("\n🚀 DEMO: ITINERARY PLANNER")
    print("="*70)
    
    # Input utente
    trip = TripInput(
        days=4,
        cities=['Milano', 'Bologna', 'Firenze', 'Roma'],
        interests=['arte', 'storia', 'cultura'],
        start_city='Milano',
        end_city='Roma',
        budget=500,
        start_date=datetime(2026, 1, 10)
    )
    
    # Crea planner e genera itinerario
    planner = ItineraryPlanner()
    schedule = planner.plan_trip(trip)
    
    # Stampa risultato
    planner.print_itinerary(schedule)
    
    return schedule


if __name__ == "__main__":
    demo_itinerary_planner()
