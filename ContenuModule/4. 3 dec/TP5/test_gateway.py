"""
Script de test pour l'API Gateway
Lance des requêtes pour tester toutes les fonctionnalités
"""
import requests
import time

# Configuration
GATEWAY_URL = "http://localhost:8000"
API_KEY = "secret-api-key-123"
HEADERS = {"X-API-Key": API_KEY}

def print_section(title):
    """Affiche un séparateur pour les sections de test"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_endpoint(name, url, headers=None):
    """Teste un endpoint et affiche le résultat"""
    print(f"\n🔹 Test : {name}")
    print(f"   URL : {url}")
    try:
        response = requests.get(url, headers=headers)
        print(f"   Statut : {response.status_code}")
        print(f"   Réponse : {response.json()}")
        return response
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return None

# ===== TEST 1 : Authentification =====
print_section("TEST 1 : Authentification")

print("\n✅ Test avec une bonne clé API :")
test_endpoint("GET /items avec clé", f"{GATEWAY_URL}/items", HEADERS)

print("\n❌ Test sans clé API (devrait être bloqué) :")
test_endpoint("GET /items sans clé", f"{GATEWAY_URL}/items")

print("\n❌ Test avec une mauvaise clé API :")
bad_headers = {"X-API-Key": "wrong-key"}
test_endpoint("GET /items avec mauvaise clé", f"{GATEWAY_URL}/items", bad_headers)

# ===== TEST 2 : Endpoints de base =====
print_section("TEST 2 : Endpoints de base")

test_endpoint("GET /users", f"{GATEWAY_URL}/users", HEADERS)
test_endpoint("GET /orders/Alice", f"{GATEWAY_URL}/orders/Alice", HEADERS)
test_endpoint("GET /items", f"{GATEWAY_URL}/items", HEADERS)

# ===== TEST 3 : Agrégation =====
print_section("TEST 3 : Agrégation de données")

test_endpoint("GET /poubelle (users + items)", f"{GATEWAY_URL}/poubelle", HEADERS)
test_endpoint("GET /profile/Alice", f"{GATEWAY_URL}/profile/Alice", HEADERS)

# ===== TEST 4 : Cache =====
print_section("TEST 4 : Cache (10 minutes)")

print("\n🔹 Première requête /users (MISS - appel au microservice) :")
test_endpoint("GET /users", f"{GATEWAY_URL}/users", HEADERS)

print("\n🔹 Deuxième requête /users (HIT - depuis le cache) :")
test_endpoint("GET /users", f"{GATEWAY_URL}/users", HEADERS)

print("\n💡 Note : Regardez les logs dans le terminal de la gateway")
print("   Vous devriez voir [CACHE MISS] puis [CACHE HIT]")

# ===== TEST 5 : Rate Limiting =====
print_section("TEST 5 : Rate Limiting (1 req / 20 sec)")

print("\n🔹 Première requête (devrait passer) :")
test_endpoint("GET /items - Requête 1", f"{GATEWAY_URL}/items", HEADERS)

print("\n🔹 Deuxième requête immédiate (devrait être bloquée) :")
response = test_endpoint("GET /items - Requête 2", f"{GATEWAY_URL}/items", HEADERS)

if response and response.status_code == 429:
    print("\n✅ Rate limiting fonctionne ! Requête bloquée (429)")
else:
    print("\n❌ Problème : le rate limiting n'a pas bloqué la requête")

print("\n⏳ Attente de 21 secondes pour réessayer...")
time.sleep(21)

print("\n🔹 Requête après 21 secondes (devrait passer) :")
test_endpoint("GET /items - Requête 3", f"{GATEWAY_URL}/items", HEADERS)

print("\n" + "="*60)
print("  TESTS TERMINÉS")
print("="*60)
