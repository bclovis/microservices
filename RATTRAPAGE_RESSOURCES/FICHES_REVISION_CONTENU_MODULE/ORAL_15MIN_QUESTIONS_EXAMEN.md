# Oral — 15 minutes — Questions de Cours + Cas Pratiques

> Format réel de l'épreuve : questions de cours ET application sur cas pratiques.  
> Couvre : microservices, FastAPI, BDD, Kafka, Gateway, Kubernetes, PokeDrafter.

---

## PARTIE A — Questions de Cours (réponse orale, ~5 min)

### Microservices

**Q1.** Quelle est la différence principale entre monolithe et microservices ? Donnez 1 avantage ET 1 inconvénient des microservices.

**Q2.** Qu'est-ce que le principe "Database per Service" ? Que se passe-t-il si deux services partagent la même base de données ?

**Q3.** Différence entre communication synchrone (REST) et asynchrone (Kafka) ? Dans quel cas choisissez-vous l'un ou l'autre ?

**Q4.** Qu'est-ce qu'un consumer group Kafka ? Que se passe-t-il si un service consumer est down quand un event est publié ?

**Q5.** Dans Kubernetes, différence entre Pod, Deployment et Service ? Pourquoi ne pas déployer directement un Pod ?

**Q6.** Qu'est-ce qu'une API Gateway ? Citez 3 fonctions qu'elle peut remplir.

---

## PARTIE B — Application sur Cas Pratiques (~10 min)

---

### CAS 1 — Concevoir une architecture microservices

**Énoncé :**
> On vous demande de construire une application de **gestion de bibliothèque en ligne**.  
> Les fonctionnalités sont : gérer les livres, gérer les membres, gérer les emprunts, envoyer des notifications email quand un livre est rendu en retard.

**Questions :**
1. Découpez en services. Listez les services et leur responsabilité.
2. Quelle base de données pour chaque service ? (SQL ou NoSQL, pourquoi ?)
3. La notification email : synchrone ou asynchrone ? Justifiez.
4. Dessinez/décrivez le schéma d'architecture (qui appelle qui, via quoi).

**Réponse attendue :**
```
Services :
- book-service      → gère le catalogue de livres       → PostgreSQL
- member-service    → gère les comptes membres           → PostgreSQL
- loan-service      → gère les emprunts/retours          → PostgreSQL
- notification-service → envoie les emails              → pas de BDD (ou Redis)

Communication :
- loan-service → REST → book-service (vérifier dispo)
- loan-service → REST → member-service (vérifier membre)
- loan-service → Kafka (topic: "loan-events") → notification-service
  (asynchrone car l'email n'a pas besoin d'être envoyé dans la même requête)

Gateway : point d'entrée unique → route vers chaque service
```

---

### CAS 2 — Lire et expliquer du code FastAPI

**Énoncé :** Qu'est-ce que ce code fait ? Identifiez les problèmes éventuels.

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db

app = FastAPI()

@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        models.User.email == user.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**Questions :**
1. Quel est le rôle de `Depends(get_db)` ?
2. Pourquoi `response_model=schemas.UserOut` et pas directement `models.User` ?
3. Ce code a un problème de sécurité — lequel ?
4. `user.dict()` est déprécié en Pydantic v2, comment l'écrire ?

**Réponses :**
1. `Depends(get_db)` = injection de dépendance → FastAPI crée et ferme la session BDD automatiquement pour chaque requête
2. `UserOut` évite d'exposer des champs sensibles (ex: `password_hash`) que le model SQLAlchemy contient
3. Le mot de passe est stocké en clair ! Il faut hasher : `bcrypt.hash(user.password)` avant de créer `db_user`
4. `user.model_dump()` en Pydantic v2

---

### CAS 3 — Dockerfile à compléter

**Énoncé :** Complétez ce Dockerfile pour un service FastAPI Python.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
# (1) Copier le fichier des dépendances
___________________________________
# (2) Installer les dépendances
___________________________________
# (3) Copier le code source
___________________________________
# (4) Exposer le port 8000
___________________________________
# (5) Lancer uvicorn sur le port 8000
___________________________________
```

**Réponse :**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Question bonus :** Pourquoi faire 2 COPY séparés (requirements.txt puis ./app) plutôt qu'un seul `COPY . .` ?
> Pour exploiter le cache Docker : si seul le code change, Docker réutilise la couche `pip install` → build beaucoup plus rapide.

---

### CAS 4 — docker-compose : trouver les bugs

**Énoncé :** Ce docker-compose a 3 bugs. Trouvez-les.

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8001"        # Bug ?
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mydb   # Bug ?
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mydb
    # volumes manquants ?                                                  # Bug ?
```

**Réponses :**
1. **Port** : `8000:8001` mais l'app tourne sur 8000 dans le container → devrait être `8000:8000`
2. **HOST** : `localhost` dans DATABASE_URL → dans Docker, `localhost` = le container lui-même, PAS la BDD. Il faut `db` (nom du service) : `postgresql://postgres:postgres@db:5432/mydb`
3. **Volume manquant** : sans volume, les données postgres sont perdues à chaque `docker compose down`. Il faut : `volumes: - postgres_data:/var/lib/postgresql/data`

---

### CAS 5 — Kubernetes : écrire un manifest

**Énoncé :** Écrivez le manifest Kubernetes pour déployer `user-service` avec :
- Image : `user-service:latest`
- 2 replicas
- Port container : 8000
- Variable d'env : `DATABASE_URL=postgresql://...`

**Réponse :**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://..."
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 8000
    targetPort: 8000
```

**Question bonus :** Pourquoi mettre le `DATABASE_URL` dans un `Secret` plutôt qu'en clair dans le Deployment ?
> Un Secret est encodé en base64 et peut être géré séparément du code. Le Deployment peut être versionné en Git sans exposer le mot de passe.

---

### CAS 6 — Raisonnement : que se passe-t-il si... ?

**Q1.** Dans PokeDrafter, le `battle_service` envoie un event Kafka après chaque bataille. Kafka est down. Que se passe-t-il ? Le combat peut-il quand même avoir lieu ?  
> Réponse attendue : oui si le code gère l'erreur gracieusement (try/except, log warning). Le combat se joue, l'event est perdu. Sans gestion d'erreur → le service crashe.

**Q2.** Un Deployment K8s a `replicas: 3`. Un des pods crashe. Que fait K8s automatiquement ?  
> K8s détecte que l'état réel (2 pods) ≠ état désiré (3 pods) → recrée un pod automatiquement. C'est le **reconciliation loop** du controller.

**Q3.** Deux services veulent lire le même topic Kafka en même temps. Ils sont dans le même consumer group. Que se passe-t-il ?  
> Kafka distribue les partitions entre les consumers du même groupe → chaque message est traité par UN SEUL consumer. Si on veut que les deux reçoivent TOUS les messages → consumer groups différents.

**Q4.** Un client envoie une requête POST sans le champ obligatoire `email`. FastAPI fait quoi ?  
> Pydantic valide automatiquement → FastAPI retourne `422 Unprocessable Entity` avec le détail du champ manquant, sans jamais exécuter la fonction.

---

## Checklist avant l'oral

- [ ] Je sais expliquer monolithe vs microservices avec un exemple
- [ ] Je sais lire un Dockerfile et expliquer chaque ligne
- [ ] Je sais identifier les bugs d'un docker-compose (ports, host, volumes)
- [ ] Je sais écrire un endpoint FastAPI avec BDD + validation + JWT
- [ ] Je sais expliquer sync vs async avec un exemple concret
- [ ] Je sais écrire un Deployment + Service K8s minimal
- [ ] Je sais expliquer ce que fait une API Gateway
- [ ] Je connais les erreurs du projet PokeDrafter et leurs causes
