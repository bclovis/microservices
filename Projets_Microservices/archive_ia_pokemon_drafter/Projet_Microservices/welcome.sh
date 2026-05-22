#!/bin/bash

# Pokemon Drafter - Welcome Banner Script

# Colors
RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Clear screen
clear

# Display banner
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗  ██████╗ ██╗  ██╗███████╗███╗   ███╗ ██████╗ ███╗   ██╗  ║
║   ██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝████╗ ████║██╔═══██╗████╗  ██║  ║
║   ██████╔╝██║   ██║█████╔╝ █████╗  ██╔████╔██║██║   ██║██╔██╗ ██║  ║
║   ██╔═══╝ ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╔╝██║██║   ██║██║╚██╗██║  ║
║   ██║     ╚██████╔╝██║  ██╗███████╗██║ ╚═╝ ██║╚██████╔╝██║ ╚████║  ║
║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝  ║
║                                                                      ║
║              ██████╗ ██████╗  █████╗ ███████╗████████╗███████╗██████╗║
║              ██╔══██╗██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
║              ██║  ██║██████╔╝███████║█████╗     ██║   █████╗  ██████╔╝
║              ██║  ██║██╔══██╗██╔══██║██╔══╝     ██║   ██╔══╝  ██╔══██╗
║              ██████╔╝██║  ██║██║  ██║██║        ██║   ███████╗██║  ██║
║              ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝  ╚═╝
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo -e "${CYAN}                    🎮 Architecture Microservices 🎮${NC}"
echo -e "${YELLOW}                          École ICC - 2026${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "                         ${RED}🔴 ÉQUIPE ROUGE 🔴${NC}"
echo "                            VS"
echo -e "                         ${BLUE}🔵 ÉQUIPE BLEUE 🔵${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Quick Commands:${NC}"
echo "  make dev-up      - Start development environment"
echo "  make build       - Build Docker images"
echo "  make deploy      - Deploy to Kubernetes"
echo "  make status      - Check deployment status"
echo "  make help        - Show all commands"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo "  README.md        - Main documentation"
echo "  QUICKSTART.md    - Quick start guide"
echo "  docs/            - Complete documentation"
echo ""
echo -e "${YELLOW}Version: 1.0.0 'Foundation'${NC}"
echo -e "${YELLOW}Date: 26 janvier 2026${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎮 Ready to battle! Choose your team and may the best trainer win! 🎮${NC}"
echo ""
