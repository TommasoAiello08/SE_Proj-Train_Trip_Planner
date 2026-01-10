from datetime import datetime
from src.dp_itinerary_planner import DPItineraryPlanner, TripInput

print('🚂 TEST PERCORSO LUNGO: Milano → Napoli (4 giorni)\n')
print('=' * 70)

planner = DPItineraryPlanner()

# Test percorso lungo con probabili fermate intermedie
trip = TripInput(
    days=4,
    start_city='Milano',
    end_city='Napoli',
    interests=['cultura', 'arte', 'storia'],
    start_date=datetime.now()
)

print(f'Pianificazione viaggio lungo:')
print(f'  Da: {trip.start_city}')
print(f'  A: {trip.end_city}')
print(f'  Giorni: {trip.days}')
print(f'  Interessi: {", ".join(trip.interests)}')
print()

try:
    result = planner.plan_trip(trip)
    
    print(f'\n✅ ITINERARIO GENERATO!\n')
    print('=' * 70)
    
    real_trains = 0
    fallback_trains = 0
    alternative_routes = 0
    
    for day in result:
        print(f'\n📅 GIORNO {day.day_number}: {day.city.upper()}')
        print(f'   Data: {day.date.strftime("%d/%m/%Y")}')
        
        if day.morning_train:
            train = day.morning_train
            
            if train.get('real_data'):
                real_trains += 1
                if train.get('via'):
                    # Percorso con cambio
                    alternative_routes += 1
                    print(f'   🚂 Treno con CAMBIO (via {train["via"]})')
                    print(f'      {day.from_city} → {train["via"]} → {day.city}')
                    print(f'      Partenza: {train["departure"]}')
                    print(f'      Arrivo: {train["arrival"]}')
                    print(f'      Durata totale: {train["travel_time"]:.1f}h (attesa cambio: {train.get("wait_time", 0):.1f}h)')
                    print(f'      Prezzo: €{train["price"]:.0f}')
                else:
                    # Treno diretto
                    print(f'   🚂 Treno DIRETTO')
                    print(f'      {day.from_city} → {day.city}')
                    print(f'      {train["train_number"]} ({train.get("train_type", "N/A")})')
                    print(f'      {train["departure"]} → {train["arrival"]} ({train["travel_time"]:.1f}h)')
                    print(f'      Prezzo: €{train["price"]:.0f}')
            else:
                fallback_trains += 1
                print(f'   🔄 Treno STIMATO (fallback geometrico)')
                print(f'      {day.from_city} → {day.city}')
                print(f'      {train["departure"]} → {train["arrival"]} ({train["travel_time"]:.1f}h)')
                print(f'      Prezzo stimato: €{train["price"]:.0f}')
        
        if day.pois:
            print(f'   🎯 Attrazioni ({len(day.pois)}):')
            for poi in day.pois:
                print(f'      • {poi["name"]} ({poi["rating"]}/10) - €{poi.get("cost_euro", 0):.0f}')
        
        print(f'   💰 Costo giornata: €{day.daily_cost:.2f}')
    
    # Statistiche finali
    total_trains = real_trains + fallback_trains
    print('\n' + '=' * 70)
    print('📊 STATISTICHE TRENI:')
    print(f'  ✅ Treni reali trovati: {real_trains}/{total_trains}')
    if alternative_routes > 0:
        print(f'  🔄 Percorsi con cambio: {alternative_routes}')
    if fallback_trains > 0:
        print(f'  ⚠️  Stime geometriche: {fallback_trains}')
    
    if total_trains > 0:
        coverage = (real_trains / total_trains) * 100
        print(f'  📈 Copertura dati reali: {coverage:.0f}%')
    
    print('\n🎉 SUCCESSO: Sistema avanzato con percorsi alternativi!')
    
except Exception as e:
    print(f'❌ Errore: {e}')
    import traceback
    traceback.print_exc()

print('=' * 70)
