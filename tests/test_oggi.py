from datetime import datetime
from src.apitr import apitr

api = apitr()

# Usa la data di OGGI secondo il sistema
oggi = datetime.now()
print(f'Data sistema: {oggi.strftime("%Y-%m-%d %H:%M")}')
print(f'Test con data corrente...\n')

# Milano
cod_milano = 'S01700'
print('Milano Centrale partenze ORA:')
partenze = api.getPartenze(cod_milano, oggi)

if partenze:
    print(f'  Trovati {len(partenze)} treni\n')
    for i, t in enumerate(partenze[:10], 1):
        num = str(t.get('numeroTreno', 'N/A'))
        cat = str(t.get('categoriaDescrizione', 'N/A'))
        dest = str(t.get('destinazione', 'N/A'))
        timestamp = t.get('orarioPartenza')
        if timestamp:
            dep_time = datetime.fromtimestamp(int(timestamp) / 1000)
            print(f'  {i:2d}. {cat:4s} {num:>5s} → {dest:35s} (parte {dep_time.strftime("%H:%M")})')
else:
    print('  ❌ Nessuna partenza')

# Verifica se qualcuno va verso zone specifiche
print('\n' + '=' * 70)
print('Analisi destinazioni:')
if partenze:
    destinazioni = {}
    for t in partenze:
        dest = t.get('destinazione', 'UNKNOWN')
        destinazioni[dest] = destinazioni.get(dest, 0) + 1
    
    for dest, count in sorted(destinazioni.items()):
        print(f'  • {dest}: {count} treni')
