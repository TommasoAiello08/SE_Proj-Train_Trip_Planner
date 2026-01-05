#!/bin/bash

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Chiusura server precedenti...${NC}"
# Chiudi tutti i processi sulle porte 5001 e 8080
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null
sleep 1

echo -e "${GREEN}✅ Server precedenti chiusi${NC}"

# Vai alla directory del progetto
cd "$(dirname "$0")"

echo -e "${BLUE}🚀 Avvio backend (porta 5001)...${NC}"
# Attiva venv e avvia backend in background
source .venv/bin/activate
python frontend/backend_server.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Aspetta che il backend sia pronto
sleep 3

echo -e "${BLUE}🌐 Avvio frontend server (porta 8080)...${NC}"
# Avvia server HTTP per frontend in background
cd frontend
python3 -m http.server 8080 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Aspetta che il server sia pronto
sleep 2

# Verifica che entrambi siano attivi
if lsof -ti:5001 > /dev/null 2>&1 && lsof -ti:8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend attivo su http://localhost:5001${NC}"
    echo -e "${GREEN}✅ Frontend attivo su http://localhost:8080${NC}"
    echo ""
    echo -e "${BLUE}📊 PID Backend: $BACKEND_PID${NC}"
    echo -e "${BLUE}📊 PID Frontend: $FRONTEND_PID${NC}"
    echo ""
    echo -e "${GREEN}🌍 Apertura browser...${NC}"
    
    # Apri nel browser (macOS)
    open "http://localhost:8080/map_planner.html"
    
    echo ""
    echo -e "${GREEN}✅ Tutto pronto!${NC}"
    echo -e "${BLUE}📝 Log backend: /tmp/backend.log${NC}"
    echo -e "${BLUE}📝 Log frontend: /tmp/frontend.log${NC}"
    echo ""
    echo -e "${RED}Per fermare i server: ./stop.sh${NC}"
else
    echo -e "${RED}❌ Errore: uno o entrambi i server non sono partiti${NC}"
    echo "Controlla i log in /tmp/backend.log e /tmp/frontend.log"
    exit 1
fi
