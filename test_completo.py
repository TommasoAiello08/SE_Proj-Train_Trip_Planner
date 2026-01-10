from datetime import datetime
from src.train_pathfinder import TrainPathfinder
from src.apitr import apitr
from src.city_database import CityDatabase

print('🎯 TEST COMPLETO PATHFINDER CON DATI REALI\n')
print('=' * 70)

api = apitr()
db = CityDatabase()
pathfinder = TrainPathfinder(api, db)

ora = datetime.now()

percorsi = [
    ('Milano', 'Bologna'),
    ('Milano', 'Roma'),
    ('Milano', 'Napoli'),
    ('Milano', 'Firenze'),
    ('Bologna', 'Firenze'),
    ('Roma', 'Napoli'),
    ('Torino', 'Milano'),
    ('Milano', 'Venezia'),
    ('Milano', 'Genova'),
]

successi = 0
fallimenti = 0

for origine, dest in percorsi:
    print(f'\n📍 {origine} → {dest}')
    print('-' * 70)
    
    try:
        result = pathfinder.find_train_route(origine, dest, ora)
        
        if result:
            print(f'✅ TROVATO!')
            print(f'   Treno {result["numero_treno"]} ({result["train"]["segments"][0]["category"]})')
            print(f'   {result["departure"]} → {result["arrival"]} ({result["travel_time"]:.1f}h)')
            print(f'   Prezzo: €{result["price"]:.0f}')
            successi += 1
        else:
            print(f'❌ Non trovato (userà fallback)')
            fallimenti += 1
    except Exception as e:
        print(f'💥 Errore: {e}')
        fallimenti += 1

print('\n' + '=' * 70)
print(f'\nRISULTATI:')
print(f'  ✅ Successi con dati reali: {successi}/{len(percorsi)}')
print(f'  ❌ Fallback necessari: {fallimenti}/{len(percorsi)}')
print(f'  📊 Percentuale successo: {successi/len(percorsi)*100:.0f}%')

if successi > 0:
    print(f'\n🎉 IL PATHFINDER FUNZIONA CON DATI API REALI!')
