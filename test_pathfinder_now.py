from datetime import datetime
from src.train_pathfinder import TrainPathfinder
from src.apitr import apitr
from src.city_database import CityDatabase

print('🧪 TEST PATHFINDER CON DATA CORRENTE\n')

api = apitr()
db = CityDatabase()
pathfinder = TrainPathfinder(api, db)

# Usa data corrente
ora_corrente = datetime.now()
print(f'Data/ora: {ora_corrente.strftime("%Y-%m-%d %H:%M")}\n')
print('=' * 70)

# Test Milano -> Bologna (dovrebbe trovare REG 2463)
print('\n📍 Test 1: Milano → Bologna')
print('-' * 70)
result = pathfinder.find_train_route('Milano', 'Bologna', ora_corrente)

if result:
    print(f'✅✅✅ SUCCESSO CON DATI REALI!')
    print(f'   Treno: {result["numero_treno"]}')
    print(f'   Partenza: {result["departure"]}')
    print(f'   Arrivo: {result["arrival"]}')
    print(f'   Durata: {result["travel_time"]:.1f}h')
    print(f'   Prezzo: €{result["price"]:.0f}')
else:
    print(f'❌ Fallito')

# Test Milano -> Reggio Calabria (FR 9587 dovrebbe passare per molte città)
print('\n📍 Test 2: Milano → Roma (via FR 9587 Reggio Calabria)')
print('-' * 70)

# Prima verifichiamo che il FR 9587 passa per Roma
print('Verifica fermate FR 9587...')
cod_milano = 'S01700'
partenze = api.getPartenze(cod_milano, ora_corrente)

fr_9587 = None
for t in partenze:
    if t.get('numeroTreno') == 9587:
        fr_9587 = t
        break

if fr_9587:
    dep_time = datetime.fromtimestamp(int(fr_9587.get('orarioPartenza')) / 1000)
    andamento = api.getAndamento(
        fr_9587.get('codOrigine'),
        '9587',
        dep_time
    )
    
    if andamento:
        fermate = andamento.get('fermate', [])
        print(f'  Fermate totali: {len(fermate)}')
        
        # Cerca Roma
        cod_roma = 'S08409'
        roma_trovata = False
        for f in fermate:
            if f.get('id') == cod_roma or 'ROMA TERMINI' in f.get('stazione', '').upper():
                roma_trovata = True
                print(f'  ✅ Passa per Roma Termini!')
                break
        
        if not roma_trovata:
            print(f'  ❌ NON passa per Roma Termini')
            # Mostra prime fermate
            print(f'  Prime fermate:')
            for f in fermate[:10]:
                print(f'    - {f.get("stazione")}')

# Test il pathfinder
result = pathfinder.find_train_route('Milano', 'Roma', ora_corrente)

if result:
    print(f'\n✅✅✅ SUCCESSO MILANO->ROMA CON DATI REALI!')
    print(f'   Treno: {result["numero_treno"]}')
    print(f'   Partenza: {result["departure"]}')
    print(f'   Arrivo: {result["arrival"]}')
    print(f'   Durata: {result["travel_time"]:.1f}h')
else:
    print(f'\n❌ Pathfinder non ha trovato il percorso')

print('\n' + '=' * 70)
