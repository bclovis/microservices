# 🌐 FICHE 08D : Nginx Gateway — Point d'entrée unique

> Basée sur le rapport (page 3) + ton vrai fichier `api/gateway/nginx.conf`.
> **Ce que tu dois dire = ce qui est dans le rapport, pas autre chose.**

---

## 🎯 PRÉSENTATION (à dire en 30 secondes)

> *"Sans gateway, le frontend devrait connaître l'adresse de chaque service. Nginx centralise le routage par préfixe d'URL et gère le proxying WebSocket. La difficulté qu'on a rencontrée : il faut ajouter les headers `Upgrade` et `Connection` explicitement pour le WebSocket, sinon le handshake échoue."*

---

## 1. Le rôle de Nginx dans notre architecture

```
AVANT (sans Nginx) :
Frontend → http://auth_service:8001/api/auth/login
Frontend → http://battle_service:8003/api/battle/battles
Frontend → http://chat_service:8005/ws/

Problèmes :
❌ Frontend connaît tous les ports internes
❌ Services directement exposés = risque sécurité
❌ CORS à configurer dans chaque service

APRÈS (avec Nginx) :
Frontend → http://localhost:80/api/auth/login    → Nginx → auth_service:8001
Frontend → http://localhost:80/api/battle/battles → Nginx → battle_service:8003
Frontend → http://localhost:80/ws/               → Nginx → chat_service:8005

Avantages :
✅ Frontend ne connaît qu'un seul point d'entrée (port 80)
✅ Services backend jamais exposés directement
✅ CORS géré à un seul endroit
```

---

## 2. Le fichier complet

**Fichier :** `api/gateway/nginx.conf`

```nginx
events {
    worker_connections 1024;   # 1024 connexions simultanées max
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    # Définition des "upstreams" (les services en amont)
    upstream auth_service    { server auth_service:8001; }
    upstream team_service    { server team_service:8002; }
    upstream battle_service  { server battle_service:8003; }
    upstream pokedex_service { server pokedex_service:8004; }
    upstream chat_service    { server chat_service:8005; }

    server {
        listen 80;   # Seul port exposé à l'extérieur

        # Routing HTTP par préfixe d'URL
        location /api/auth    { proxy_pass http://auth_service/api/auth; }
        location /api/teams   { proxy_pass http://team_service/api/teams; }
        location /api/battle  { proxy_pass http://battle_service/api/battle; }
        location /api/pokedex { proxy_pass http://pokedex_service/api/pokedex; }
        location /api/chat    { proxy_pass http://chat_service/api/chat; }

        # Routing WebSocket — configuration SPÉCIALE
        location /ws/ {
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_pass http://chat_service;
        }
    }
}
```

---

## 3. Le routing HTTP — Comment ça marche

**Exemple : `POST http://localhost/api/battle/battles/`**

```
1. Nginx reçoit la requête sur le port 80
2. Il regarde le préfixe → /api/battle → correspond au bloc "location /api/battle"
3. Il proxy vers http://battle_service:8003/api/battle/battles/
4. battle_service traite, retourne la réponse
5. Nginx retransmet au client
```

**Le principe `upstream` :**
```nginx
upstream battle_service { server battle_service:8003; }
```
- `battle_service` = nom du service Docker
- Nginx résout ce nom via le réseau interne Docker
- Avantage : si on ajoute une 2ème instance, Nginx fait du load balancing automatiquement

---

## 4. ⚠️ La partie WebSocket — LA DIFFICULTÉ RENCONTRÉE

**Ce qu'il faut dire (du rapport) :**
> *"Nginx centralise le routage par préfixe d'URL et gère le proxying WebSocket, ce qui n'est pas trivial : il faut ajouter les headers `Upgrade` et `Connection` explicitement, sinon le handshake échoue (c'est d'ailleurs une des difficultés rencontrées)."*

### Pourquoi le WebSocket est différent du HTTP normal ?

**HTTP normal :**
```
Client → Requête → Serveur → Réponse → Connexion fermée
```

**WebSocket :**
```
Client → "Je veux passer en WebSocket" (handshake)
Serveur → "OK, je passe en WebSocket"
Client ←→ Serveur (connexion ouverte indéfiniment, messages dans les 2 sens)
```

Le handshake HTTP ressemble à ça :
```
GET /ws/ HTTP/1.1
Upgrade: websocket         ← "Je veux passer en WebSocket"
Connection: Upgrade        ← "C'est une demande d'upgrade"
```

### Le problème avec Nginx

**Par défaut**, Nginx en mode proxy **supprime** les headers `Upgrade` et `Connection`.

Résultat sans la config WebSocket :
```
Client → Upgrade: websocket
Nginx  → (supprime Upgrade et Connection)
chat_service → Reçoit une requête HTTP normale → refuse le WebSocket
Client → Erreur 101 Protocol Switch Failed
```

### La solution

```nginx
location /ws/ {
    proxy_http_version 1.1;           # HTTP/1.1 obligatoire (WebSocket ne marche pas en HTTP/1.0)
    proxy_set_header Upgrade $http_upgrade;     # Retransmet le header Upgrade
    proxy_set_header Connection "upgrade";       # Retransmet Connection: upgrade
    proxy_pass http://chat_service;
}
```

**Résultat avec la config :**
```
Client → Upgrade: websocket
Nginx  → Retransmet Upgrade + Connection
chat_service → Reçoit le handshake → Accepte le WebSocket ✅
Connexion WebSocket établie !
```

### Pourquoi `$http_upgrade` ?

`$http_upgrade` est une variable Nginx qui contient la valeur du header `Upgrade` de la requête entrante.
- Si le client envoie `Upgrade: websocket` → `$http_upgrade = "websocket"`
- Nginx retransmet exactement cette valeur au service

---

## 5. Sécurité — Réseau fermé

**Ce qu'il faut dire (du rapport page 5) :**
> *"Le réseau Docker est fermé : seul Nginx est accessible depuis l'extérieur. Les services backend communiquent entre eux via le réseau interne Docker, sans exposition directe."*

**En pratique dans docker-compose.yml :**
- `gateway` expose le port `80:80` (hôte:conteneur)
- `auth_service` expose `8001:8000` **uniquement pour le dev/debug**
- En production, on enlèverait les ports exposés des services, seul Nginx serait accessible

---

## 🔥 QUESTIONS PROBABLES SUR Nginx

| Question | Réponse courte |
|----------|---------------|
| "Pourquoi Nginx ?" | Point d'entrée unique, services backend non exposés directement |
| "Comment Nginx route les requêtes ?" | Par préfixe d'URL : /api/auth → auth_service, /api/battle → battle_service |
| "Pourquoi des headers spéciaux pour WebSocket ?" | Nginx supprime Upgrade/Connection par défaut, le handshake échoue sans eux |
| "C'est quoi `proxy_http_version 1.1` ?" | WebSocket ne fonctionne qu'en HTTP/1.1, pas HTTP/1.0 |
| "Quelle difficulté rencontrée ?" | WebSocket ne passait pas à cause des headers Upgrade/Connection |
| "C'est quoi un upstream ?" | Définition du service cible, permet du load balancing si plusieurs instances |
| "Comment les services backend sont protégés ?" | Ils ne sont pas exposés directement, tout passe par Nginx sur le port 80 |
