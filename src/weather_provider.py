"""
Weather Provider - OpenWeatherMap API Integration
Provides weather forecasts for cities to influence itinerary planning
"""

import requests
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json


class WeatherProvider:
    """
    Provider for weather data with caching
    Uses OpenWeatherMap API (free tier: 60 calls/min, 1000/day)
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_hours: int = 6):
        """
        Initialize weather provider
        
        Args:
            api_key: OpenWeatherMap API key (if None, uses demo mode)
            cache_hours: Hours to cache weather data (default 6h)
        """
        self.api_key = api_key or "DEMO_MODE"  # Replace with real key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.cache_dir = Path(__file__).parent.parent / "cache" / "weather"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_hours)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
    
    def _rate_limit(self):
        """Apply rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, city_name: str) -> Path:
        """Get cache file path for a city"""
        safe_name = city_name.replace(" ", "_").lower()
        return self.cache_dir / f"{safe_name}_weather.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid"""
        if not cache_path.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < self.cache_ttl
    
    def _load_from_cache(self, city_name: str) -> Optional[Dict]:
        """Load weather data from cache"""
        cache_path = self._get_cache_path(city_name)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def _save_to_cache(self, city_name: str, data: Dict):
        """Save weather data to cache"""
        cache_path = self._get_cache_path(city_name)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving weather cache: {e}")
    
    def get_forecast(self, city_name: str, lat: float, lon: float, days: int = 5) -> Optional[Dict]:
        """
        Get weather forecast for a city
        
        Args:
            city_name: City name for caching
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast (max 5 for free tier)
            
        Returns:
            Dict with daily forecasts or None
        """
        # Check cache first
        cached = self._load_from_cache(city_name)
        if cached:
            print(f"  💾 Weather cache hit for {city_name}")
            return cached
        
        # Demo mode - return simulated data
        if self.api_key == "DEMO_MODE":
            print(f"  🎭 Demo mode: simulating weather for {city_name}")
            return self._get_demo_weather(city_name, days)
        
        # Real API call
        print(f"  🌤️  Fetching weather for {city_name}...")
        
        try:
            self._rate_limit()
            
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 data points per day (3h intervals)
            }
            
            response = requests.get(
                f"{self.base_url}/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Process forecast data
            forecast = self._process_forecast(data, days)
            
            # Cache it
            self._save_to_cache(city_name, forecast)
            
            return forecast
            
        except Exception as e:
            print(f"  ⚠️  Weather API error for {city_name}: {e}")
            # Fallback to demo data
            return self._get_demo_weather(city_name, days)
    
    def _process_forecast(self, api_data: Dict, days: int) -> Dict:
        """Process OpenWeatherMap API response into daily summaries"""
        daily_forecasts = {}
        
        for item in api_data.get('list', [])[:days*8]:
            # Extract date
            dt = datetime.fromtimestamp(item['dt'])
            date_key = dt.strftime('%Y-%m-%d')
            
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = {
                    'date': date_key,
                    'temps': [],
                    'conditions': [],
                    'rain_prob': []
                }
            
            # Collect data
            daily_forecasts[date_key]['temps'].append(item['main']['temp'])
            daily_forecasts[date_key]['conditions'].append(item['weather'][0]['main'])
            daily_forecasts[date_key]['rain_prob'].append(item.get('pop', 0) * 100)
        
        # Compute daily averages
        result = {}
        for date_key, data in daily_forecasts.items():
            result[date_key] = {
                'date': date_key,
                'temp_avg': round(sum(data['temps']) / len(data['temps']), 1),
                'temp_min': round(min(data['temps']), 1),
                'temp_max': round(max(data['temps']), 1),
                'condition': max(set(data['conditions']), key=data['conditions'].count),
                'rain_probability': round(sum(data['rain_prob']) / len(data['rain_prob']), 0),
                'is_rainy': max(data['rain_prob']) > 50,
                'is_sunny': 'Clear' in data['conditions'] or 'Clouds' in data['conditions']
            }
        
        return result
    
    def _get_demo_weather(self, city_name: str, days: int) -> Dict:
        """
        Generate simulated weather data for demo/testing
        Varies by city and season
        """
        # Simple simulation based on city latitude (rough approximation)
        northern_cities = ['Milano', 'Torino', 'Venezia', 'Verona', 'Bologna']
        
        forecasts = {}
        base_date = datetime.now()
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            
            # Vary weather by day and city
            is_rainy = (hash(city_name + date_key) % 100) < 30  # 30% rain chance
            temp_base = 15 if city_name in northern_cities else 18
            temp_variation = (hash(date_key) % 10) - 5
            
            forecasts[date_key] = {
                'date': date_key,
                'temp_avg': temp_base + temp_variation,
                'temp_min': temp_base + temp_variation - 3,
                'temp_max': temp_base + temp_variation + 5,
                'condition': 'Rain' if is_rainy else ('Clouds' if (hash(date_key) % 2) else 'Clear'),
                'rain_probability': 70 if is_rainy else 20,
                'is_rainy': is_rainy,
                'is_sunny': not is_rainy
            }
        
        return forecasts
    
    def get_weather_for_date(self, city_name: str, lat: float, lon: float, target_date: datetime) -> Optional[Dict]:
        """
        Get weather for a specific date
        
        Args:
            city_name: City name
            lat: Latitude
            lon: Longitude
            target_date: Date to get weather for
            
        Returns:
            Weather dict for that date or None
        """
        # Get forecast
        days_ahead = (target_date.date() - datetime.now().date()).days
        
        if days_ahead < 0 or days_ahead > 5:
            print(f"  ⚠️  Weather forecast only available for next 5 days")
            return None
        
        forecast = self.get_forecast(city_name, lat, lon, days=min(days_ahead + 1, 5))
        
        if forecast:
            date_key = target_date.strftime('%Y-%m-%d')
            return forecast.get(date_key)
        
        return None
    
    def classify_weather_for_poi(self, weather: Dict) -> str:
        """
        Classify weather suitability for POI selection
        
        Returns:
            'indoor' - prefer indoor activities
            'outdoor' - good for outdoor activities  
            'mixed' - suitable for both
        """
        if not weather:
            return 'mixed'
        
        if weather.get('is_rainy'):
            return 'indoor'
        elif weather.get('is_sunny') and weather.get('temp_avg', 15) > 10:
            return 'outdoor'
        else:
            return 'mixed'


# Test
if __name__ == "__main__":
    print("🌤️  Weather Provider Test\n")
    
    provider = WeatherProvider()  # Demo mode
    
    # Test cities
    test_cities = [
        ('Milan', 45.4642, 9.1900),
        ('Rome', 41.9028, 12.4964),
        ('Florence', 43.7696, 11.2558)
    ]
    
    for city, lat, lon in test_cities:
        print(f"\n{'='*60}")
        print(f"🏛️  {city.upper()}")
        print('='*60)
        
        forecast = provider.get_forecast(city, lat, lon, days=5)
        
        if forecast:
            print(f"\n📅 5-Day Forecast:")
            for date_key, data in sorted(forecast.items())[:5]:
                emoji = '🌧️' if data['is_rainy'] else ('☀️' if data['is_sunny'] else '☁️')
                print(f"  {emoji} {data['date']}: {data['temp_avg']}°C "
                      f"({data['temp_min']}°-{data['temp_max']}°C) - "
                      f"{data['condition']} ({data['rain_probability']:.0f}% rain)")
                
                classification = provider.classify_weather_for_poi(data)
                print(f"     → POI preference: {classification}")
        else:
            print("  ❌ No forecast available")
    
    print(f"\n{'='*60}")
    print("✅ Weather Provider Test Complete")
    print('='*60)
