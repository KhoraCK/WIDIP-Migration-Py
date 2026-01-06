#!/bin/bash

echo "========================================"
echo "   WIBOT - Arret"
echo "========================================"
echo

# Aller dans le repertoire du script
cd "$(dirname "$0")"

# Arreter le frontend (processus npm/node sur port 5173)
echo "[1/2] Arret du frontend..."
pkill -f "vite" 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Arreter le backend Docker
echo "[2/2] Arret du backend Docker..."
cd wibot-backend
docker compose down

echo
echo "========================================"
echo "   WIBOT arrete !"
echo "========================================"
echo
