# 🖥️ FICHE 11 — FLOW FRONTEND & ENDPOINTS APPELÉS

> **Framework :** Angular (standalone components)
> **Source de vérité :** `web/src/app/` du GitHub Latest

---

## PAGES DE L'APPLICATION (routes Angular)

| URL | Composant | Accessible sans login ? |
|-----|-----------|------------------------|
| `/auth/login` | LoginComponent | ✅ Oui |
| `/auth/register` | RegisterComponent | ✅ Oui |
| `/dashboard/play` | BattleArenaComponent | ❌ (guard JWT) |
| `/dashboard/teams` | TeamListComponent | ❌ |
| `/dashboard/teams/build` | TeamBuilderComponent | ❌ |
| `/dashboard/dex` | PokedexListComponent | ❌ |

---

## FLOW COMPLET D'UNE PARTIE — PAS À PAS

### ÉTAPE 0 — Connexion

**Page `/auth/login` :**
- L'utilisateur entre username + password
- Clic sur "Se connecter"
- → `POST /auth/login` → reçoit `{access_token, refresh_token, token_type}`
- Token stocké en mémoire (AuthService)
- Redirect vers `/dashboard/play`

---

### ÉTAPE 1 — Sélection du mode (Phase `selection`)

**Page `/dashboard/play` — boutons visibles :**

| Bouton | Ce que ça fait |
|--------|---------------|
| **Draft** | Sélectionne le mode `pioche` |
| **Constructed** | Sélectionne le mode `construit` + affiche un dropdown pour choisir son équipe |
| **Hazard** | Sélectionne le mode `hasard` |
| **Start Match** | Lance le matchmaking (désactivé si Constructed sans équipe sélectionnée) |

**Au clic "Start Match" — logique de matchmaking :**

```
1. GET /battle/battles/open
   → récupère les salles "en_attente"

   SI une salle du même mode existe (et ce n'est pas ta propre salle) :
     → WebSocket connect("blue")
     → POST /battle/battles/{id}/join   { player_blue_id: currentUser.id }
     → transition vers phase "battle"

   SINON (aucune salle disponible) :
     → WebSocket connect("red")
     → POST /battle/battles/            { player_red_id, mode }
     → POLL toutes les 2s : GET /battle/battles/{id}
       jusqu'à ce que player_blue_id soit renseigné
     → transition vers phase "battle"
```

---

### ÉTAPE 2 — Draft (uniquement mode Draft, Phase `drafting`)

**Ce que le joueur voit :** 12 Pokémon aléatoires affichés en grille

**Ce que le joueur fait :**
- Clic sur un Pokémon → il est "pris" (grisé)
- Tours alternés : Rouge choisit → Bleu choisit → Rouge → Bleu...
- Quand tous les 12 sont pris → transition automatique vers phase "battle"

**Endpoints appelés :**
- `GET /pokedex/pokemon/random?count=12` → charge le pool de draft

*(En mode Random : 2x `GET /pokedex/pokemon/random?count=6` — une équipe par joueur)*
*(En mode Constructed : l'équipe vient des teams déjà chargées au démarrage)*

---

### ÉTAPE 3 — Combat (Phase `battle`)

**Ce que le joueur voit :**
- Scoreboard : `scoreRed — scoreBlue` + numéro du round
- Pokémon actif adverse (avec sprite) + son équipe en haut
- Ton Pokémon actif (avec sprite) + ton équipe en bas
- Timer de tour

**Boutons et actions :**

| Action | Bouton | Endpoint appelé |
|--------|--------|----------------|
| Choisir un Pokémon de son équipe | Clic sur la carte Pokémon | (local, sélection seulement) |
| Changer de Pokémon + attaquer | **"Switch & Attack"** | `POST /battle/battles/{id}/turn` |
| Garder son Pokémon actif + attaquer | **"Rester"** | `POST /battle/battles/{id}/turn` |
| Abandonner | **"Déclarer Forfait"** | `POST /battle/battles/{id}/forfeit` |

**Payload envoyé à `/turn` :**
```json
{
  "pokemon_red": "Salameche",
  "pokemon_blue": "Bulbizarre",
  "types_red": ["Feu"],
  "types_blue": ["Plante", "Poison"]
}
```

**Ce qui se passe après `/turn` :**
- `result === "A"` → Rouge gagne le tour → `scoreRed++` → Pokémon bleu KO → adversaire change
- `result === "B"` → Bleu gagne le tour → `scoreBlue++` → Pokémon rouge KO → joueur doit changer
- `result === "draw"` → les deux restent, round suivant
- Si toute l'équipe adverse KO → `POST /battle/battles/{id}/end` → phase `finished`

**Timer :**
- Timer visible dans le composant `BattleTimerComponent`
- Si timeout → `onTimeout()` → joue le tour automatiquement avec le Pokémon actif

---

### ÉTAPE 4 — Fin de partie (Phase `finished`)

**Ce que le joueur voit :**
- `"Victory!"` / `"Defeat"` / `"Draw"` selon le `winner`
- `"You crushed your opponent and earned 10 points!"` ou le contraire

**Boutons :**

| Bouton | Ce que ça fait |
|--------|---------------|
| **Play Again** | Reset complet → retour phase `selection` |
| **Dashboard** | Navigue vers `/dashboard` |

---

## RÉCAP DES ENDPOINTS APPELÉS PAR LE FRONTEND

| Endpoint | Méthode | Quand | Service backend |
|----------|---------|-------|----------------|
| `/auth/login` | POST | Page login | auth_service |
| `/auth/register` | POST | Page register | auth_service |
| `/team/teams/` | GET | Chargement équipes (mode Constructed) | team_service |
| `/battle/battles/open` | GET | Clic "Start Match" | battle_service |
| `/battle/battles/` | POST | Créer une salle (si aucune dispo) | battle_service |
| `/battle/battles/{id}/join` | POST | Rejoindre une salle existante | battle_service |
| `/battle/battles/{id}` | GET | Polling (attente adversaire) toutes les 2s | battle_service |
| `/battle/battles/{id}/turn` | POST | Clic "Switch & Attack" ou "Rester" | battle_service |
| `/battle/battles/{id}/end` | POST | Quand toute l'équipe adverse est KO | battle_service |
| `/battle/battles/{id}/forfeit` | POST | Clic "Déclarer Forfait" | battle_service |
| `/pokedex/pokemon/random` | GET | Modes Draft et Random | pokedex_service |
| `ws://.../ws/chat/{team}` | WebSocket | Dès que le match est trouvé | chat_service |

---

## COMMENT LE JWT CIRCULE

```
1. Login → reçoit access_token
2. JwtInterceptor Angular intercepte TOUS les appels HTTP
   → ajoute automatiquement : Authorization: Bearer <token>
3. Chaque service backend (auth, team, battle...) vérifie le JWT
   dans son propre dependencies.py
4. Nginx ne vérifie PAS le JWT — il route seulement
```

**Fichier Angular :** `core/interceptors/jwt.interceptor.ts`

---

## REMARQUES IMPORTANTES À CONNAÎTRE

**Le matchmaking n'est pas en temps réel :**
- Le polling toutes les 2s (`GET /battle/battles/{id}`) est une approche basique
- En prod on utiliserait un WebSocket ou Server-Sent Events pour notifier "adversaire trouvé"

**Le draft est local, pas synchronisé entre les deux joueurs :**
- Les picks se font en local sur le navigateur (variable `isRedTurn` en mémoire)
- En prod, chaque pick devrait passer par le serveur pour que les deux joueurs voient la même chose en temps réel

**L'adversaire en mode Constructed est toujours random :**
```typescript
// initConstructed()
const blue = await firstValueFrom(this.pokedexService.getRandomPokemon(6));
// ← l'adversaire ne choisit pas son équipe, il a 6 Pokémon aléatoires
```
C'est une simplification notable du projet.
