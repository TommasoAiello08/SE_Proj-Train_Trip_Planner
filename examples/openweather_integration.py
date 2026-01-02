"""
Esempio di Integrazione OpenWeather API
Dimostra come combinare dati meteo con il planner di viaggi
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class OpenWeatherClient:
    """Client per OpenWeather API"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: str):
        """
        Inizializza il client OpenWeather
        
        Args:
            api_key: API key ottenuta da https://openweathermap.org/api
                    (Free tier: 60 calls/min, 1,000,000 calls/month)
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ConstraintBasedTrainPlanner/1.0'
        })
    
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """
        Ottieni meteo corrente per coordinate
        
        Args:
            lat: Latitudine
            lon: Longitudine
        
        Returns:
            Dict con dati meteo correnti
        """
        url = f"{self.BASE_URL}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric',  # Celsius
            'lang': 'it'
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_forecast(self, lat: float, lon: float) -> List[Dict]:
        """
        Ottieni previsioni per i prossimi 5 giorni (step 3h)
        
        Args:
            lat: Latitudine
            lon: Longitudine
        
        Returns:
            Lista di previsioni ogni 3 ore
        """
        url = f"{self.BASE_URL}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'it'
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('list', [])
    
    def get_weather_at_time(self, lat: float, lon: float, target_time: datetime) -> Optional[Dict]:
        """
        Ottieni previsione meteo per un orario specifico
        
        Args:
            lat: Latitudine
            lon: Longitudine
            target_time: Orario target
        
        Returns:
            Previsione meteo più vicina all'orario target
        """
        forecasts = self.get_forecast(lat, lon)
        
        # Trova la previsione più vicina all'orario target
        closest_forecast = None
        min_diff = float('inf')
        
        for forecast in forecasts:
            forecast_time = datetime.fromtimestamp(forecast['dt'])
            diff = abs((forecast_time - target_time).total_seconds())
            
            if diff < min_diff:
                min_diff = diff
                closest_forecast = forecast
        
        return closest_forecast
    
    def format_weather(self, weather_data: Dict) -> str:
        """
        Formatta dati meteo in stringa leggibile
        
        Args:
            weather_data: Dati meteo da API
        
        Returns:
            Stringa formattata
        """
        if not weather_data:
            return "Meteo non disponibile"
        
        temp = weather_data.get('main', {}).get('temp', 'N/A')
        feels_like = weather_data.get('main', {}).get('feels_like', 'N/A')
        description = weather_data.get('weather', [{}])[0].get('description', 'N/A')
        humidity = weather_data.get('main', {}).get('humidity', 'N/A')
        wind_speed = weather_data.get('wind', {}).get('speed', 'N/A')
        
        return f"""
🌤️  Condizioni: {description.capitalize()}
🌡️  Temperatura: {temp}°C (percepita: {feels_like}°C)
💧 Umidità: {humidity}%
💨 Vento: {wind_speed} m/s
        """.strip()


class WeatherConstraint:
    """Constraint basato su condizioni meteo"""
    
    def __init__(self, weather_client: OpenWeatherClient):
        self.weather_client = weather_client
    
    def evaluate_for_trip(self, origin_coords: tuple, dest_coords: tuple, 
                          departure_time: datetime, arrival_time: datetime) -> Dict:
        """
        Valuta condizioni meteo per un viaggio
        
        Args:
            origin_coords: (lat, lon) origine
            dest_coords: (lat, lon) destinazione
            departure_time: Orario partenza
            arrival_time: Orario arrivo
        
        Returns:
            Dict con valutazione meteo
        """
        # Meteo alla partenza
        weather_origin = self.weather_client.get_weather_at_time(
            origin_coords[0], origin_coords[1], departure_time
        )
        
        # Meteo all'arrivo
        weather_dest = self.weather_client.get_weather_at_time(
            dest_coords[0], dest_coords[1], arrival_time
        )
        
        return {
            'origin': {
                'weather': weather_origin,
                'time': departure_time,
                'suitable': self._is_suitable(weather_origin)
            },
            'destination': {
                'weather': weather_dest,
                'time': arrival_time,
                'suitable': self._is_suitable(weather_dest)
            }
        }
    
    def _is_suitable(self, weather_data: Optional[Dict]) -> bool:
        """
        Determina se le condizioni meteo sono adatte
        
        Args:
            weather_data: Dati meteo
        
        Returns:
            True se condizioni accettabili
        """
        if not weather_data:
            return True  # Nessun dato = assume OK
        
        # Condizioni da evitare
        bad_conditions = ['thunderstorm', 'snow', 'extreme']
        
        weather_main = weather_data.get('weather', [{}])[0].get('main', '').lower()
        
        for condition in bad_conditions:
            if condition in weather_main:
                return False
        
        # Controlla temperatura estrema
        temp = weather_data.get('main', {}).get('temp', 20)
        if temp < -5 or temp > 40:
            return False
        
        return True


# ============================================================================
# ESEMPIO D'USO
# ============================================================================

def demo_weather_integration():
    """
    Demo completa di integrazione OpenWeather con il planner
    
    NOTA: Richiede API key OpenWeather (gratuita)
    Registrati su: https://openweathermap.org/api
    """
    
    # ⚠️ IMPORTANTE: Inserisci qui la tua API key
    API_KEY = "YOUR_API_KEY_HERE"
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  ATTENZIONE: Inserisci una API key valida per OpenWeather")
        print("   Registrati gratuitamente su: https://openweathermap.org/api")
        print()
        print("Demo con dati mock...")
        demo_with_mock_data()
        return
    
    # Inizializza client
    weather_client = OpenWeatherClient(API_KEY)
    
    # Coordinate stazioni
    milano_centrale = (45.4865, 9.2039)
    roma_termini = (41.9009, 12.5028)
    
    print("="*70)
    print("INTEGRAZIONE OPENWEATHER - Demo")
    print("="*70)
    
    # 1. Meteo corrente a Milano
    print("\n1️⃣  METEO CORRENTE - Milano Centrale")
    print("-"*70)
    current = weather_client.get_current_weather(*milano_centrale)
    print(weather_client.format_weather(current))
    
    # 2. Previsione per viaggio
    print("\n2️⃣  PREVISIONE PER VIAGGIO - Milano → Roma")
    print("-"*70)
    departure = datetime.now() + timedelta(hours=2)
    arrival = departure + timedelta(hours=3)
    
    print(f"Partenza: {departure.strftime('%Y-%m-%d %H:%M')}")
    print(f"Arrivo: {arrival.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Meteo alla partenza
    weather_dep = weather_client.get_weather_at_time(*milano_centrale, departure)
    print("🚂 Meteo alla PARTENZA (Milano):")
    print(weather_client.format_weather(weather_dep))
    print()
    
    # Meteo all'arrivo
    weather_arr = weather_client.get_weather_at_time(*roma_termini, arrival)
    print("🏁 Meteo all'ARRIVO (Roma):")
    print(weather_client.format_weather(weather_arr))
    
    # 3. Valutazione constraint
    print("\n3️⃣  VALUTAZIONE CONSTRAINT METEO")
    print("-"*70)
    constraint = WeatherConstraint(weather_client)
    evaluation = constraint.evaluate_for_trip(
        milano_centrale, roma_termini, departure, arrival
    )
    
    origin_suitable = evaluation['origin']['suitable']
    dest_suitable = evaluation['destination']['suitable']
    
    print(f"✅ Condizioni alla partenza: {'ADATTE' if origin_suitable else '⚠️ NON ADATTE'}")
    print(f"✅ Condizioni all'arrivo: {'ADATTE' if dest_suitable else '⚠️ NON ADATTE'}")
    
    if origin_suitable and dest_suitable:
        print("\n🎉 VIAGGIO CONSIGLIATO: Condizioni meteo favorevoli!")
    else:
        print("\n⚠️  VIAGGIO DA VALUTARE: Condizioni meteo non ottimali")
    
    print("\n" + "="*70)


def demo_with_mock_data():
    """Demo con dati mock quando API key non è disponibile"""
    
    print("\n" + "="*70)
    print("DEMO CON DATI MOCK (no API key)")
    print("="*70)
    
    # Simula dati meteo
    mock_weather = {
        'main': {
            'temp': 18.5,
            'feels_like': 17.2,
            'humidity': 65
        },
        'weather': [
            {'description': 'cielo sereno', 'main': 'Clear'}
        ],
        'wind': {
            'speed': 3.2
        }
    }
    
    print("\n🌤️  Esempio dati meteo che il sistema utilizzerebbe:")
    print("-"*70)
    
    # Crea client dummy
    class DummyWeatherClient:
        def format_weather(self, data):
            return OpenWeatherClient('dummy').format_weather(data)
    
    client = DummyWeatherClient()
    print(client.format_weather(mock_weather))
    
    print("\n💡 Con una API key reale, il sistema:")
    print("   1. Otterrebbe previsioni per orario partenza/arrivo")
    print("   2. Valuterebbe condizioni meteo (pioggia, neve, temperatura)")
    print("   3. Consiglierebbe o sconsigliare il viaggio")
    print("   4. Suggerirebbe orari alternativi con meteo migliore")
    
    print("\n" + "="*70)


# ============================================================================
# INTEGRAZIONE CON IL PLANNER
# ============================================================================

class WeatherAwareTripPlanner:
    """
    Planner di viaggi che tiene conto del meteo
    
    Estende il planner base con constraint meteo
    """
    
    def __init__(self, weather_api_key: Optional[str] = None):
        self.weather_enabled = weather_api_key is not None
        if self.weather_enabled:
            self.weather_client = OpenWeatherClient(weather_api_key)
            self.weather_constraint = WeatherConstraint(self.weather_client)
    
    def plan_trip_with_weather(self, origin, destination, departure_time,
                               station_coords: Dict[str, tuple]):
        """
        Pianifica viaggio considerando meteo
        
        Args:
            origin: Stazione origine
            destination: Stazione destinazione
            departure_time: Orario partenza
            station_coords: Dict {station_name: (lat, lon)}
        
        Returns:
            Soluzioni con valutazione meteo
        """
        if not self.weather_enabled:
            print("⚠️  Weather integration non abilitata (manca API key)")
            return None
        
        # Ottieni coordinate
        origin_coords = station_coords.get(origin)
        dest_coords = station_coords.get(destination)
        
        if not origin_coords or not dest_coords:
            print(f"❌ Coordinate non disponibili per {origin} o {destination}")
            return None
        
        # Stima arrivo (semplificato, in realtà viene dall'API)
        arrival_time = departure_time + timedelta(hours=3)
        
        # Valuta meteo
        weather_eval = self.weather_constraint.evaluate_for_trip(
            origin_coords, dest_coords, departure_time, arrival_time
        )
        
        return weather_eval


def demo_full_integration():
    """Demo completa con planner + meteo"""
    
    print("\n" + "="*70)
    print("DEMO INTEGRAZIONE COMPLETA: Planner + Meteo")
    print("="*70)
    
    # Coordinate stazioni (da database o API Trenitalia)
    station_coords = {
        'MILANO CENTRALE': (45.4865, 9.2039),
        'ROMA TERMINI': (41.9009, 12.5028),
        'FIRENZE SANTA MARIA NOVELLA': (43.7763, 11.2478)
    }
    
    # Crea planner (senza API key per demo)
    planner = WeatherAwareTripPlanner(weather_api_key=None)
    
    print("\n💡 SCENARIO: Viaggio Milano → Roma domani alle 10:00")
    print("-"*70)
    print("Il sistema:")
    print("1. Cerca soluzioni di viaggio (API Trenitalia)")
    print("2. Per ogni soluzione, valuta meteo a partenza/arrivo")
    print("3. Filtra soluzioni con maltempo (constraint hard)")
    print("4. Ordina per condizioni meteo favorevoli (constraint soft)")
    print("5. Suggerisce orari alternativi se meteo migliore")
    
    print("\n📊 ESEMPIO OUTPUT:")
    print("-"*70)
    print("""
Soluzione 1: FR 9615 (10:00 → 13:00) ⭐⭐⭐⭐⭐
  🌤️  Partenza: Cielo sereno, 20°C
  🌤️  Arrivo: Parzialmente nuvoloso, 22°C
  ✅ CONSIGLIATO

Soluzione 2: IC 605 (10:30 → 13:55)  ⭐⭐⭐
  🌧️  Partenza: Pioggia leggera, 18°C
  🌤️  Arrivo: Cielo sereno, 23°C
  ⚠️  Da valutare

Soluzione 3: REG 2050 (11:00 → 15:30) ⭐
  ⛈️  Partenza: Temporale, 17°C
  🌧️  Arrivo: Pioggia, 20°C
  ❌ SCONSIGLIATO (maltempo)
    """)
    
    print("="*70)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     OpenWeather API Integration - Train Trip Planner        ║
    ║              Esempio di Integrazione Meteo                   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Esegui demo
    demo_weather_integration()
    
    print("\n")
    input("Premi ENTER per vedere l'integrazione completa...")
    
    demo_full_integration()
    
    print("\n✅ Demo completata!")
    print("\n💡 PROSSIMI PASSI:")
    print("   1. Registra un account gratuito su https://openweathermap.org")
    print("   2. Ottieni la tua API key")
    print("   3. Sostituisci 'YOUR_API_KEY_HERE' con la tua chiave")
    print("   4. Riesegui lo script per testare con dati reali")
    print("\n📚 Documentazione: https://openweathermap.org/api/one-call-3")
