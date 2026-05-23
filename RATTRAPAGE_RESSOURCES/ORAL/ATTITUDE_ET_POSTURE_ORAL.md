# 🎯 ATTITUDE ET POSTURE À L'ORAL

> **Contexte :** Tu repasses l'oral après un 5/20. Le prof sait que le projet avait des problèmes. L'objectif n'est pas de convaincre que tout était parfait — c'est de montrer que tu comprends le sujet MAINTENANT.

---

## CE QUE LE PROF ÉVALUE À L'ORAL

L'oral rattrapage n'est pas une punition. C'est une deuxième chance de montrer ta compréhension. Ce que Raphaël LALANNE cherche :

1. **Tu comprends les concepts** (microservices, Kafka, Docker, K8s)
2. **Tu comprends TON code** (même imparfait — tu l'expliques et tu vois ses limites)
3. **Tu es honnête** sur ce qui n'a pas marché

Ce qu'il ne cherche PAS :
- Un projet parfait (il sait que tu as eu 5/20)
- Un discours appris par cœur
- Des excuses longues

---

## SUR L'UTILISATION DE L'IA

### Ne dis rien si on ne te demande pas

Si le prof ne pose pas la question, ne l'amène pas toi-même. Ce n'est pas le sujet.

### Si le prof demande : "Vous avez utilisé l'IA ?"

**Ne nie pas, ne te justifie pas en excès.** Réponse courte et directe :

> "Oui, on a utilisé des outils d'IA pour des parties du code, notamment pour la structure de base et certains fichiers de config. Ce qui était important pour moi c'était de comprendre ce que le code faisait — c'est pour ça que j'ai travaillé à comprendre chaque partie."

Puis **enchaîne immédiatement sur une démonstration de compréhension** :
> "Par exemple, dans battle_service, le producer Kafka est lazy — il n'est pas créé au démarrage parce que..."

Ça coupe court au sujet IA et montre que tu as bossé pour comprendre.

### Ce que tu ne dis PAS

❌ "L'IA a tout fait, j'ai rien compris"
❌ "Je savais pas que c'était interdit"
❌ Une longue justification défensive — ça fait pire impression que l'aveu lui-même

---

## SUR LE RENDU EN RETARD

### Si le prof le mentionne

Réponse courte, sans sur-expliquer :

> "Oui, on a rendu en retard — on a eu du mal à finaliser les services et ça a impacté la qualité du rendu aussi."

Puis passe à autre chose. Ne détaille pas les raisons personnelles sauf si il insiste. Le prof ne veut pas une histoire — il veut voir si tu as progressé depuis.

---

## SUR LE 5/20 ET LES ERREURS DU CODE

### Ce qui était faux dans le projet (tu peux le dire toi-même)

Le fait de nommer les erreurs AVANT que le prof les pointe = tu montres que tu les as comprises.

**Formule utile :**
> "On avait des problèmes dans le projet — notamment les routes battle n'avaient pas d'authentification, ce qui est une erreur importante. Ce qu'il aurait fallu faire, c'est ajouter un `Depends(get_current_user)` et vérifier que l'utilisateur est bien un des joueurs de la bataille."

Ça fait une impression très différente de "je sais pas pourquoi j'ai 5".

### Les 3 erreurs à citer spontanément si le sujet vient

1. **Pas d'auth sur les routes battle** → "Manquait `get_current_user` + vérification ownership"
2. **Pas de tests** → "On a testé manuellement avec Postman, pas de pytest"
3. **`battle_ended` non publié sur Kafka** → "La route `/end` ne publie rien, c'est une lacune"

---

## POSTURE GÉNÉRALE PENDANT LES 30 MINUTES

### ✅ Ce qui marche

**Prendre 3-5 secondes avant de répondre**
Le silence de réflexion = tu cherches la vraie réponse. C'est bien vu.

**Dire "je ne suis pas sûr mais je dirais que..."**
Bien mieux que d'inventer ou de se taire. Le prof voit que tu raisonnes.

**Relier au code réel**
Quand tu expliques un concept, ancre-le dans ton code :
> "Dans notre projet, on voit ça dans `kafka_service.py` ligne 12, où le producer est créé seulement si `_producer is None`."

**Montrer ce que tu changerais**
> "Ce qu'on aurait amélioré c'est..."
Ça montre que tu comprends les limites, pas juste ce qui marche.

---

### ❌ Ce qui fait mauvaise impression

**Inventer une réponse**
Le prof voit immédiatement. Et ça casse la confiance pour le reste de l'oral.

**Dire "j'ai pas eu le temps"** pour tout
Une fois c'est acceptable. Trois fois ça ressemble à une excuse générale.

**Lire tes notes pendant une question**
Avoir des notes avec toi c'est ok. Les lire mot à mot = pas de compréhension.

**Défendre une erreur que tu ne comprends pas**
Si le prof dit "ça c'est un problème" et tu réponds "non c'est normal" sans savoir pourquoi → mauvais. Mieux vaut dire "vous avez raison, c'est un point faible".

---

## SCRIPT POUR L'OUVERTURE DES 15 MIN PROJET

Quand le prof dit "présentez votre partie du projet" :

> "J'ai travaillé sur battle_service, chat_service, et la partie infrastructure — Docker Compose et Kubernetes.
>
> battle_service gère la logique des combats : création de batailles, tours de jeu avec calcul d'avantage de types, et publication d'events Kafka à chaque tour.
>
> chat_service reçoit ces events Kafka et les diffuse en temps réel via WebSocket aux joueurs connectés.
>
> Les deux communiquent de façon asynchrone par Kafka — battle_service ne sait pas que chat_service existe, il publie juste sur le topic `battle-events`.
>
> Je peux détailler n'importe laquelle de ces parties."

Après ça, laisse le prof choisir ce qu'il veut creuser. Ne fais pas un monologue.

---

## COMMENT RÉPONDRE QUAND TU BLOQUES

| Situation | Ce que tu dis |
|-----------|--------------|
| Tu ne sais pas du tout | "Je ne suis pas sûr de ça — je saurais chercher dans la doc mais de mémoire je ne peux pas répondre avec certitude." |
| Tu sais à moitié | "Je dirais que... [ta réponse partielle] — mais je ne suis pas à 100% sûr de la partie sur [ce qui manque]." |
| Le prof pointe une erreur | "Oui vous avez raison, c'est un point qu'on n'a pas bien géré. Ce qu'on aurait dû faire c'est..." |
| Question hors de ta partie | "Ça c'était la partie de [collègue] — sur ma partie je peux vous expliquer..." |

---

## EN RÉSUMÉ : LES 3 CHOSES QUI FONT PASSER L'ORAL

1. **Comprendre ton code** — pas le réciter, l'expliquer avec tes mots
2. **Voir les limites** — nommer les erreurs avant que le prof les pointe
3. **Rester calme** — une question difficile n'est pas un piège, c'est une opportunité de montrer que tu réfléchis
