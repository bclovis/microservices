# Erreurs Rencontrées — PokeDrafter (et comment les expliquer à l'oral)

> Fiche de débogage réelle : toutes ces erreurs ont été rencontrées en lançant le projet PokeDrafter.  
> Pour chaque erreur : ce qui s'est passé, pourquoi, et comment le justifier face au professeur.

---

## Erreur 1 — `database "chat_db" does not exist`

### Ce qui s'affiche
```
asyncpg.exceptions.InvalidCatalogNameError: database "chat_db" does not exist
```
Le `chat_service` crashe en boucle (Restarting) dès le démarrage.

### Pourquoi ça arrive
Le fichier `infra/scripts/init-db.sql` contient bien :
```sql
CREATE DATABASE auth_db;
CREATE DATABASE team_db;
CREATE DATABASE battle_db;
CREATE DATABASE chat_db;
```

Mais **PostgreSQL n'exécute les scripts d'initialisation que lors du tout premier démarrage**, quand le répertoire de données est vide.

Si un volume Docker `postgres_data` existait déjà d'une exécution précédente (avant que `chat_db` soit ajoutée), PostgreSQL démarre sur les données existantes et **n'exécute plus jamais `init.sql`** → `chat_db` n'existe pas.

### Diagnostic
```bash
# Vérifier les bases qui existent vraiment
docker exec -it docker-postgres-1 psql -U postgres -c "\l"
```
→ Si `chat_db` n'est pas dans la liste = le volume est ancien.

### Fix
```bash
# Supprimer les volumes + recréer tout proprement
docker compose down -v
docker compose up --build -d
```
`-v` = supprime aussi les volumes → PostgreSQL repart à zéro → `init.sql` s'exécute → toutes les bases sont créées.

### Ce qu'il faut dire à l'oral
> "PostgreSQL n'exécute les scripts `docker-entrypoint-initdb.d/` qu'à la première initialisation du data directory. Si le volume `postgres_data` existait déjà d'une session précédente, l'init script ne tourne pas → la base `chat_db` n'est jamais créée. Solution : `docker compose down -v` pour purger le volume et forcer la réinitialisation."

---

## Erreur 2 — Services inaccessibles depuis le navigateur (port mapping incorrect)

### Ce qui s'affiche
- `http://localhost:8001/docs` → **Site inaccessible** dans le navigateur
- `curl http://localhost:8001/docs` → **Empty reply from server**
- Pourtant `docker compose ps` montre tous les services **Up**

### Pourquoi ça arrive
Mismatch entre le port dans le Dockerfile et le port mappé dans `docker-compose.yml` :

| Fichier | Ce qui est configuré |
|---------|---------------------|
| `auth_service/Dockerfile` | `CMD ["uvicorn", ..., "--port", "8001"]` → écoute sur **8001** dans le container |
| `docker-compose.yml` | `ports: "8001:8000"` → mappe host:8001 → container:**8000** |

**Résultat :** les requêtes arrivent sur le container port 8000, mais personne n'écoute sur 8000 → réponse vide.

### Diagnostic
```bash
# Voir ce que fait le docker-proxy (le "routeur" de Docker)
ps aux | grep docker-proxy | grep 8001
# → affiche -container-port 8000 = Docker envoie vers 8000

# Vérifier depuis l'intérieur du container (où ça marche)
docker exec docker-auth_service-1 python -c "
import urllib.request
r = urllib.request.urlopen('http://localhost:8001/docs')
print('Status:', r.status)
"
# → Status: 200 ✅ (ça marche en interne, pas depuis l'extérieur)
```

### Fix
Dans `infra/docker/docker-compose.yml`, corriger les mappings :
```yaml
# AVANT (incorrect)
auth_service:
  ports:
    - "8001:8000"   # container:8000 ≠ uvicorn port 8001

# APRÈS (correct)
auth_service:
  ports:
    - "8001:8001"   # host:8001 → container:8001 ✅
```
À faire pour les 5 services : auth(8001), team(8002), battle(8003), pokedex(8004), chat(8005).

Puis redémarrer :
```bash
docker compose up -d --no-build  # --no-build = pas besoin de rebuilder les images
```

### Ce qu'il faut dire à l'oral
> "Le `docker-compose.yml` mappait `8001:8000` — soit host:8001 vers container:8000 — mais uvicorn dans le container écoutait sur le port 8001 selon le Dockerfile. Le docker-proxy de Docker routait donc vers un port vide. La commande `ps aux | grep docker-proxy` permet de le vérifier. Le fix est d'aligner les ports dans docker-compose avec ceux configurés dans les Dockerfiles."

---

## Commandes de diagnostic générales (à connaître)

```bash
# 1. Voir l'état de tous les containers
docker compose ps

# 2. Voir les logs d'un service qui crashe
docker compose logs <service> --tail 50

# 3. Entrer dans un container
docker exec -it <container_name> bash
# ou pour un container slim sans bash :
docker exec -it <container_name> sh

# 4. Accéder à PostgreSQL depuis un container
docker exec -it docker-postgres-1 psql -U postgres

# 5. Commandes psql utiles
\l          -- lister les bases
\c auth_db  -- se connecter à une base
\dt         -- lister les tables
SELECT * FROM users;

# 6. Voir les ports réellement ouverts sur la machine
ss -tlnp | grep 8001

# 7. Voir comment Docker route les ports
ps aux | grep docker-proxy

# 8. Redémarrer sans rebuilder les images
docker compose up -d --no-build

# 9. Tout supprimer (containers + volumes) et repartir à zéro
docker compose down -v
```

---

## Comment ce bug a pu passer inaperçu ? (Important à expliquer à l'oral)

### Pour l'erreur 1 — `chat_db` (volume existant)

Ce bug ne se voit **que si on avait déjà lancé le projet avant** que `chat_db` soit ajoutée.

- En développement, le développeur a d'abord lancé le projet avec 3 bases (auth, team, battle)
- Le volume `postgres_data` a été créé
- Plus tard, `chat_service` + `chat_db` ont été ajoutés au projet
- Le développeur a fait `docker compose up` → les services redémarrent mais **le volume existe déjà** → init.sql ne tourne pas → bug silencieux
- Sur une **machine fraîche** (premier clone du repo), ça marche parfaitement → le développeur ne voit pas le problème chez lui

> **Leçon :** Ce type de bug est un *"works on my machine"* classique. Il ne se reproduit que si on a un état résiduel. C'est pour ça qu'il faut toujours tester avec `docker compose down -v` avant de livrer.

### Pour l'erreur 2 — Port mismatch (8001:8000)

Ce bug vient d'une **convention mal appliquée**.

La convention Docker standard est : tous les services tournent sur **port 8000 en interne**, et on les expose sur des ports différents en externe :
```yaml
auth_service:  ports: "8001:8000"  # convention ✅
team_service:  ports: "8002:8000"  # convention ✅
```

Le développeur a correctement configuré le docker-compose selon cette convention. **Mais** il a oublié d'adapter les Dockerfiles — ceux-ci lancent uvicorn sur des ports spécifiques (8001, 8002...) au lieu du port standard 8000.

Le bug passe inaperçu parce que :
1. Les services démarrent sans erreur → `docker compose ps` montre **Up** → tout semble OK
2. Le crash n'est pas dans les logs du service (uvicorn tourne correctement)
3. Il faut tester manuellement chaque URL pour remarquer le problème
4. Si le développeur teste depuis l'intérieur d'un container (ex: gateway → auth_service) ça peut fonctionner autrement selon la config réseau

> **Leçon :** Un container "Up" ne veut pas dire "accessible". Il faut toujours valider end-to-end : `curl http://localhost:8001/docs` depuis la machine hôte.

---

## Principe clé à retenir pour l'oral

> **"En microservices Docker, il faut toujours que le port EXPOSE dans le Dockerfile, le port `--port` d'uvicorn, et le port container dans docker-compose soient cohérents."**

```
Dockerfile:        EXPOSE 8001   +   CMD --port 8001
docker-compose:    ports: "8001:8001"
                          ↑host  ↑container
```

Si l'un des trois ne correspond pas → service inaccessible depuis l'extérieur.
