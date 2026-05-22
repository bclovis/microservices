#!/usr/bin/env python3
"""
Script de validation du projet TP5
Vérifie que tous les fichiers nécessaires sont présents
"""

import os
import sys
from pathlib import Path

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file(filepath, description):
    """Vérifie qu'un fichier existe"""
    if os.path.exists(filepath):
        print(f"  {GREEN}✓{RESET} {description}")
        return True
    else:
        print(f"  {RED}✗{RESET} {description} - MANQUANT")
        return False

def check_directory(dirpath, description):
    """Vérifie qu'un dossier existe"""
    if os.path.isdir(dirpath):
        print(f"  {GREEN}✓{RESET} {description}")
        return True
    else:
        print(f"  {RED}✗{RESET} {description} - MANQUANT")
        return False

def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  VALIDATION DU PROJET TP5 - API GATEWAY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    all_ok = True
    
    # Structure des dossiers
    print(f"{YELLOW}📁 Structure des dossiers{RESET}")
    all_ok &= check_directory("users", "Dossier users/")
    all_ok &= check_directory("orders", "Dossier orders/")
    all_ok &= check_directory("gateway", "Dossier gateway/")
    
    # Fichiers Python des microservices
    print(f"\n{YELLOW}🐍 Microservices Python{RESET}")
    all_ok &= check_file("users/main.py", "users/main.py")
    all_ok &= check_file("users/__init__.py", "users/__init__.py")
    all_ok &= check_file("orders/main.py", "orders/main.py")
    all_ok &= check_file("orders/__init__.py", "orders/__init__.py")
    all_ok &= check_file("gateway/main.py", "gateway/main.py")
    all_ok &= check_file("gateway/__init__.py", "gateway/__init__.py")
    
    # Fichiers de configuration
    print(f"\n{YELLOW}⚙️  Configuration{RESET}")
    all_ok &= check_file("requirements.txt", "requirements.txt")
    all_ok &= check_file(".gitignore", ".gitignore")
    
    # Scripts utilitaires
    print(f"\n{YELLOW}🛠️  Scripts{RESET}")
    all_ok &= check_file("test_gateway.py", "test_gateway.py")
    all_ok &= check_file("start_services.sh", "start_services.sh")
    
    # Documentation
    print(f"\n{YELLOW}📚 Documentation{RESET}")
    all_ok &= check_file("README.md", "README.md")
    all_ok &= check_file("EXPLICATIONS.md", "EXPLICATIONS.md")
    all_ok &= check_file("ARCHITECTURE.md", "ARCHITECTURE.md")
    all_ok &= check_file("CURL_COMMANDS.md", "CURL_COMMANDS.md")
    all_ok &= check_file("QUICK_START.md", "QUICK_START.md")
    
    # Vérification du contenu de gateway/main.py
    print(f"\n{YELLOW}🔍 Vérification des fonctionnalités{RESET}")
    
    try:
        with open("gateway/main.py", "r") as f:
            content = f.read()
            
        features = [
            ("verify_api_key", "Middleware d'authentification API Key"),
            ("rate_limiter", "Middleware de rate limiting"),
            ("get_from_cache", "Système de cache"),
            ("CACHE_DURATION", "Expiration du cache (10 min)"),
            ("RATE_LIMIT_SECONDS", "Limite de requêtes (20 sec)"),
            ("/poubelle", "Endpoint d'agrégation /poubelle"),
            ("/profile/", "Endpoint d'agrégation /profile"),
        ]
        
        for keyword, description in features:
            if keyword in content:
                print(f"  {GREEN}✓{RESET} {description}")
            else:
                print(f"  {RED}✗{RESET} {description} - MANQUANT")
                all_ok = False
                
    except FileNotFoundError:
        print(f"  {RED}✗{RESET} Impossible de lire gateway/main.py")
        all_ok = False
    
    # Résumé
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_ok:
        print(f"{GREEN}✅ VALIDATION RÉUSSIE !{RESET}")
        print(f"\n{BLUE}Prochaines étapes :{RESET}")
        print(f"  1. Installer les dépendances : pip install -r requirements.txt")
        print(f"  2. Lancer les services (voir QUICK_START.md)")
        print(f"  3. Tester : python test_gateway.py")
    else:
        print(f"{RED}❌ VALIDATION ÉCHOUÉE{RESET}")
        print(f"\nCertains fichiers ou fonctionnalités sont manquants.")
        return 1
    
    print(f"{BLUE}{'='*60}{RESET}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
