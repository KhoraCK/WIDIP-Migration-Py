#!/bin/bash

# Couleurs ANSI
CYAN='\033[0;96m'
YELLOW='\033[0;93m'
GREEN='\033[0;92m'
RED='\033[0;91m'
MAGENTA='\033[0;95m'
BLUE='\033[0;94m'
WHITE='\033[0;97m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

clear
echo ""
echo -e "${CYAN}███████╗███████╗███████╗███████╗███████╗███████╗███████╗███████╗███████╗███████╗${NC}"
echo -e "${CYAN}██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝${NC}"
echo -e "${CYAN}██║     ██║     ██║     ██║     ██║     ██║     ██║     ██║     ██║     ██║     ${NC}"
echo -e "${YELLOW}██║  ███╗██║  ███╗██║  ███╗██║  ███╗██║  ███╗██║  ███╗██║  ███╗██║  ███╗██║  ███╗██║  ███╗${NC}"
echo -e "${YELLOW}██║   ██║██║   ██║██║   ██║██║   ██║██║   ██║██║   ██║██║   ██║██║   ██║██║   ██║██║   ██║${NC}"
echo -e "${YELLOW}╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝${NC}"
echo -e "${YELLOW} ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝ ${NC}"
echo ""
echo -e "                      ${MAGENTA}██╗    ██╗${RED}██╗${GREEN}██████╗  ██████╗ ████████╗${NC}"
echo -e "                      ${MAGENTA}██║    ██║${RED}██║${GREEN}██╔══██╗██╔═══██╗╚══██╔══╝${NC}"
echo -e "                      ${MAGENTA}██║ █╗ ██║${RED}██║${GREEN}██████╔╝██║   ██║   ██║   ${NC}"
echo -e "                      ${MAGENTA}██║███╗██║${RED}██║${GREEN}██╔══██╗██║   ██║   ██║   ${NC}"
echo -e "                      ${MAGENTA}╚███╔███╔╝${RED}██║${GREEN}██████╔╝╚██████╔╝   ██║   ${NC}"
echo -e "                      ${MAGENTA} ╚══╝╚══╝ ${RED}╚═╝${GREEN}╚═════╝  ╚═════╝    ╚═╝   ${NC}"
echo ""
echo -e "                  ${WHITE}╔═══════════════════════════════════════╗${NC}"
echo -e "                  ${WHITE}║   ${CYAN}Chatbot IA Intelligent - WIDIP${WHITE}     ║${NC}"
echo -e "                  ${WHITE}╚═══════════════════════════════════════╝${NC}"
echo ""
echo ""

# Aller dans le repertoire du script
cd "$(dirname "$0")"

# Demarrer le backend (Docker)
echo -e "${GREEN}►${NC} [1/2] ${YELLOW}Demarrage du backend Docker...${NC}"
cd wibot-backend
docker compose up -d

echo ""
echo -e "${CYAN}⏳ Attente du demarrage des services (15 secondes)...${NC}"
sleep 15

# Demarrer le frontend
echo ""
echo -e "${GREEN}►${NC} [2/2] ${YELLOW}Demarrage du frontend React...${NC}"
cd ../wibot-frontend
npm run dev &

echo ""
echo ""
echo -e "${GREEN}███████████████████████████████████████████████████████████${NC}"
echo -e "${GREEN}█${NC}                                                         ${GREEN}█${NC}"
echo -e "${GREEN}█${NC}  ${CYAN}✓ WIBOT démarré avec succès !${NC}                        ${GREEN}█${NC}"
echo -e "${GREEN}█${NC}                                                         ${GREEN}█${NC}"
echo -e "${GREEN}███████████████████████████████████████████████████████████${NC}"
echo ""
echo -e "   ${MAGENTA}🌐 Frontend${NC}      : ${WHITE}http://localhost:5173${NC}"
echo -e "   ${YELLOW}⚙️  n8n Editor${NC}    : ${WHITE}http://localhost:5679${NC}"
echo -e "   ${CYAN}🗄️  PostgreSQL${NC}    : ${WHITE}localhost:5432${NC}"
echo ""
echo -e "   ${RED}👤 Identifiants par défaut${NC}"
echo -e "      Username : ${GREEN}khora${NC}"
echo -e "      Password : ${GREEN}test123${NC}"
echo ""
echo -e "${GRAY}────────────────────────────────────────────────────────────${NC}"
echo ""
