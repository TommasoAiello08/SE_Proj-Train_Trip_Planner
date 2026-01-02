# 🚀 Quick Start - Italian Train Trip Planner

## Avvio Rapido (2 minuti)

### Passo 1: Installazione
```bash
git clone <repository-url>
cd SEProejct
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Passo 2: Avvia Backend
```bash
python frontend/backend_server.py
```

✅ Vedi questo? **Perfetto!**
```
🚂 Starting Italian Train Trip Planner Backend...
 * Running on http://127.0.0.1:5001
```

⚠️ **NON CHIUDERE QUESTO TERMINALE**

### Passo 3: Apri Frontend
Doppio click su: `frontend/map_planner.html`

Oppure da terminale:
```bash
open frontend/map_planner.html  # macOS
```

## 🎯 Primo Utilizzo

1. **Clicca** una città sulla mappa (es. Milano)
2. **Imposta** data e durata (es. 2 giorni)
3. **Seleziona** interessi (opzionale)
4. **Clicca** "🔍 Pianifica Viaggio"
5. **Fatto!** 🎉

## ❌ Problemi?

### "Failed to fetch"
👉 Il backend non è attivo. Torna al **Passo 2**.

### Porta 5001 occupata
```bash
lsof -i :5001
kill -9 <PID>
python frontend/backend_server.py
```

### Altro?
Leggi il [README.md](README.md) completo.

---

**Enjoy! 🚂**
