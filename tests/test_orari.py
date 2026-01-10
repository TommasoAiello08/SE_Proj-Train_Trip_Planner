from datetime import datetime
from src.apitr import apitr

api = apitr()
cod_milano = 'S01700'

print('🔍 RICERCA TRENI MILANO -> ROMA/NAPOLI A VARI ORARI\n')
print('=' * 70)

# Prova vari orari della giornata
orari_test = [
    (6, 0, "Mattina presto"),
    (7, 0, "Prima mattina"),
    (8, 0, "Mattina"),
    (9, 0, "Tarda mattina"),
    (12, 0, "Mezzogiorno"),
    (14, 0, "Pomeriggio"),
    (16, 0, "Tardo pomeriggio"),
    (18, 0, "Sera"),
]

for ora, minuti, desc in orari_test:
    date = datetime(2025, 1, 10, ora, minuti, 0)
    
    print(f'\n{desc} ({ora}:{minuti:02d}):')
    print('-' * 70)
    
    partenze = api.getPartenze(cod_milano, date)
    
    if not partenze:
        print('  ❌ Nessuna partenza')
        continue
    
    # Cerca treni verso Sud (Roma, Napoli, Firenze)
    treni_sud = []
    for t in partenze:
        dest = t.get('destinazione', '').upper()
        if any(citta in dest for citta in ['ROMA', 'NAPOLI', 'FIRENZE', 'SALERNO']):
            treni_sud.append(t)
    
    if treni_sud:
        print(f'  ✅ Trovati {len(treni_sud)} treni verso Sud:')
        for t in treni_sud[:5]:  # Max 5
            num = t.get('numeroTreno')
            cat = t.get('categoriaDescrizione', 'N/A')
            dest = t.get('destinazione')
            timestamp = t.get('orarioPartenza')
            if timestamp:
                dep_time = datetime.fromtimestamp(int(timestamp) / 1000)
                print(f'    • {cat:3s} {num:5s} → {dest:30s} (parte {dep_time.strftime("%H:%M")})')
    else:
        print(f'  ⚠️  {len(partenze)} treni ma nessuno verso Sud')

print('\n' + '=' * 70)
print('Test completato')
