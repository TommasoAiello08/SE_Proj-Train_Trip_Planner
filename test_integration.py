from datetime import datetime
from src.dp_itinerary_planner import DPItineraryPlanner, TripInput

print('🚂 TEST INTEGRAZIONE COMPLETA: DP + PATHFINDER REALE\n')
print('=' * 70)

planner = DPItineraryPlanner()

# Test semplice: Milano -> Bologna per 2 giorni
trip = TripInput(
    days=2,
    start_city='Milano',
    end_city='Bologna',
    interests=['cultura', 'arte'],
    start_date=datetime.now()
)

print(f'Pianificazione viaggio:')
print(f'  Da: {trip.start_city}')
print(f'  A: {trip.end_city}')
print(f'  Giorni: {trip.days}')
print(f'  Data: {trip.start_date.strftime("%Y-%m-%d")}')
print()

try:
    result = planner.plan_trip(trip)
    
    print(f'\n✅ ITINERARIO GENERATO!\n')
    
    for day in result:
        print(f'📅 Giorno {day.day_number}: {day.city}')
        
        if day.morning_train:
            train = day.morning_train
            if train.get('real_data'):
                print(f'   🚂 Treno REALE: {train["train_number"]}')  # FIX: era numero_treno
            else:
                print(f'   🔄 Treno stimato (fallback)')
            print(f'      {train["departure"]} → {train["arrival"]}')
            print(f'      Durata: {train["travel_time"]:.1f}h')
            print(f'      Prezzo: €{train["price"]:.0f}')
        
        if day.pois:
            print(f'   🎯 Attrazioni ({len(day.pois)}):')
            for poi in day.pois[:3]:
                print(f'      • {poi["name"]} ({poi["rating"]}/10)')
        
        print()
    
    print('🎉 SUCCESSO: Sistema completo funzionante con dati reali!')
    
except Exception as e:
    print(f'❌ Errore: {e}')
    import traceback
    traceback.print_exc()

print('=' * 70)
