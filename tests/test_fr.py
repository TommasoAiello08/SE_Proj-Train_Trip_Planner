from datetime import datetime
from src.apitr import apitr

api = apitr()
cod_milano = 'S01700'
cod_roma = 'S08409'
date = datetime(2025, 1, 10, 10, 0, 0)

print('DEBUG: Analisi FR 8807 verso Taranto')
print('(Alta Velocità, dovrebbe passare per Roma)\n')

partenze = api.getPartenze(cod_milano, date)
treno_8807 = None

for t in partenze:
    if t.get('numeroTreno') == 8807:
        treno_8807 = t
        break

if treno_8807:
    print(f'✅ Trovato Frecciarossa 8807')
    print(f'  Categoria: {treno_8807.get("categoriaDescrizione")}')
    print(f'  Destinazione: {treno_8807.get("destinazione")}')
    
    dep_time = datetime.fromtimestamp(int(treno_8807.get('orarioPartenza')) / 1000)
    print(f'  Partenza: {dep_time}')
    
    print(f'\nAndamento FR 8807:')
    andamento = api.getAndamento(
        treno_8807.get('codOrigine'),
        '8807',
        dep_time
    )
    
    if andamento:
        fermate = andamento.get('fermate', [])
        print(f'  Fermate totali: {len(fermate)}\n')
        
        roma_trovata = False
        for i, f in enumerate(fermate):
            staz = f.get('stazione', 'N/A')
            id_staz = f.get('id', 'N/A')
            
            # Evidenzia Roma
            marker = ''
            if id_staz == cod_roma or 'ROMA TERMINI' in staz.upper():
                marker = ' ✅ ROMA TERMINI!'
                roma_trovata = True
                print(f'  {i+1:2d}. {staz:45s} (ID: {id_staz}){marker}')
                arr_teorico = f.get('arrivo_teorico')
                if arr_teorico:
                    arr_time = datetime.fromtimestamp(int(arr_teorico) / 1000)
                    print(f'      Arrivo: {arr_time}')
                    durata = (arr_time - dep_time).total_seconds() / 3600
                    print(f'      Durata: {durata:.1f}h')
            elif 'ROMA' in staz.upper():
                marker = ' ← Roma (altra stazione)'
                print(f'  {i+1:2d}. {staz:45s} (ID: {id_staz}){marker}')
            else:
                print(f'  {i+1:2d}. {staz:45s} (ID: {id_staz})')
        
        print(f'\n{"✅ Roma Termini trovata" if roma_trovata else "❌ Roma Termini NON trovata"}')
    else:
        print('  ❌ Andamento non disponibile')
else:
    print('❌ Treno 8807 non trovato nelle partenze')
    print('\nTutti i treni FR disponibili:')
    for t in partenze:
        if 'FR' in t.get('categoriaDescrizione', ''):
            print(f'  FR {t.get("numeroTreno")} -> {t.get("destinazione")}')
