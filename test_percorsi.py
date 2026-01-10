from datetime import datetime
from src.train_pathfinder import TrainPathfinder
from src.apitr import apitr
from src.city_database import CityDatabase

print('🧪 TEST PATHFINDER: PERCORSI BREVI\n')
print('=' * 70)

api = apitr()
db = CityDatabase()
pathfinder = TrainPathfinder(api, db)

# Test percorsi brevi che dovrebbero funzionare
percorsi_test = [
    ('Milano', 'Bologna', 'Percorso breve frequente'),
    ('Bologna', 'Firenze', 'Alta velocità frequente'),
    ('Roma', 'Napoli', 'Alta velocità frequente'),
    ('Torino', 'Milano', 'Percorso breve frequente'),
    ('Milano', 'Venezia', 'Percorso breve'),
]

date = datetime(2025, 1, 10, 10, 0, 0)

for origine, dest, descrizione in percorsi_test:
    print(f'\n📍 {origine} → {dest}')
    print(f'   {descrizione}')
    print('-' * 70)
    
    try:
        result = pathfinder.find_train_route(origine, dest, date)
        
        if result:
            print(f'✅ PERCORSO TROVATO!')
            print(f'   Partenza: {result["departure"]}')
            print(f'   Arrivo: {result["arrival"]}')
            print(f'   Durata: {result["travel_time"]:.1f}h')
            print(f'   Treno: {result["numero_treno"]} ({result["train"]["segments"][0]["category"]})')
            print(f'   Prezzo: €{result["price"]:.0f}')
            print(f'   🎯 DATI REALI API')
        else:
            print(f'❌ Nessun percorso trovato')
            print(f'   (userà fallback geometrico)')
    except Exception as e:
        print(f'💥 ERRORE: {e}')

print('\n' + '=' * 70)
