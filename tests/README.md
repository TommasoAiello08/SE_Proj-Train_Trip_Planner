# Test Suite - Italian Train Trip Planner

Test files per verificare funzionalità del sistema di pianificazione itinerari.

## Test Principali

### `test_integration.py` ⭐ **Test Completo Sistema**
Test end-to-end dell'intero pipeline DP + PathFinder con dati reali.
- **Percorso**: Milano → Bologna (2 giorni)
- **Verifica**: Coverage dati reali, fallback, statistiche
- **Uso**: `python tests/test_integration.py`

### `test_lungo.py` ⭐ **Test Percorsi Lunghi**
Test sistema su itinerari multi-città con percorsi alternativi.
- **Percorso**: Milano → Napoli (4 giorni)
- **Verifica**: Ricerca alternative, cambi, statistiche dettagliate
- **Uso**: `python tests/test_lungo.py`

### `test_completo.py` **Test PathFinder Multi-Rotta**
Verifica TrainPathfinder su 9 percorsi comuni italiani.
- **Percorsi**: Milano→Bologna, Milano→Roma, Bologna→Firenze, etc.
- **Metriche**: Percentuale successo, durate reali, prezzi
- **Uso**: `python tests/test_completo.py`

## Test API e Debug

### `test_percorsi.py` - Test Percorsi Brevi
Verifica funzionamento pathfinder su tratte brevi (<300km).

### `test_fr.py` - Debug Treni Frecciarossa
Analizza fermate specifiche di treni ad alta velocità (es. FR 8807).

### `test_oggi.py` - Test Data Corrente
Verifica API Trenitalia con data/ora del sistema attuale.

### `test_orari.py` - Test Fasce Orarie
Prova ricerca treni in vari momenti della giornata (6:00-18:00).

### `test_pathfinder_now.py` - Test PathFinder Tempo Reale
Esegue pathfinder con timestamp corrente del sistema.

## Come Eseguire

```bash
# Attiva virtual environment
source .venv/bin/activate  # macOS/Linux
# o: .venv\Scripts\activate  # Windows

# Singolo test
python tests/test_integration.py

# Test multipli
python tests/test_completo.py && python tests/test_lungo.py
```

## Risultati Attesi

### test_integration.py
```
✅ Itinerario generato: 2 giorni
📈 Copertura dati reali: 1/1 tratte (100%)
🎉 SUCCESSO: Sistema completo funzionante con dati reali!
```

### test_lungo.py
```
📊 STATISTICHE TRENI:
  ✅ Treni reali trovati: 1/3
  🔄 Percorsi con cambio: 0
  ⚠️  Stime geometriche: 2
  📈 Copertura dati reali: 33%
```

### test_completo.py
```
✅ Successi con dati reali: 6/9
❌ Fallback necessari: 3/9
📊 Percentuale successo: 67%
```

## Note Tecniche

- **Limitazione API**: Trenitalia API ritorna solo dati per data corrente
- **Timeout**: PathFinder ha timeout di 15s per evitare hang
- **Caching**: Train cache è persistente durante sessione
- **Fallback**: Sistema usa stima geometrica se API fallisce

## Troubleshooting

**Problema**: "❌ Nessuna partenza trovata"
- **Causa**: API Trenitalia non ha dati per quella data/ora
- **Soluzione**: Usa `datetime.now()` invece di date future

**Problema**: Test lento (>60s)
- **Causa**: Pathfinder analizza troppi treni
- **Soluzione**: Controlla timeout in `src/train_pathfinder.py`

**Problema**: Coverage basso (<50%)
- **Causa**: API instabile o percorsi senza treni diretti
- **Soluzione**: Normale per distanze >400km, sistema usa fallback
