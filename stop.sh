#!/bin/bash

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}🛑 Fermando i server...${NC}"

# Chiudi tutti i processi sulle porte 5001 e 8080
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

sleep 1

echo -e "${GREEN}✅ Server fermati${NC}"
