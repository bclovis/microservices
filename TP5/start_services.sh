#!/bin/bash

# Script de lancement des 3 microservices
# Utilisation : ./start_services.sh

echo "🚀 Démarrage des microservices..."
echo ""

# Couleurs pour les logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Instructions :${NC}"
echo "1. Ouvrez 3 terminaux séparés"
echo "2. Dans chaque terminal, lancez une des commandes suivantes :"
echo ""

echo -e "${GREEN}Terminal 1 - Users Service (port 8001) :${NC}"
echo "uvicorn users.main:app --port 8001"
echo ""

echo -e "${GREEN}Terminal 2 - Orders Service (port 8002) :${NC}"
echo "uvicorn orders.main:app --port 8002"
echo ""

echo -e "${GREEN}Terminal 3 - Gateway (port 8000) :${NC}"
echo "uvicorn gateway.main:app --port 8000"
echo ""

echo -e "${YELLOW}⚠️  Lancez d'abord les services users et orders, puis la gateway !${NC}"
echo ""

echo -e "${BLUE}🧪 Pour tester l'API :${NC}"
echo "python test_gateway.py"
echo ""
echo "ou consultez CURL_COMMANDS.md pour les commandes manuelles"
