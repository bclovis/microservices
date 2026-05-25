# =============================================================================
# BATTLE SERVICE — services/battle_engine.py
# Moteur de jeu : calcul des avantages de type Pokémon (formule F(A))
# =============================================================================
# RÔLE DU FICHIER :
# Ce fichier contient TOUTE la logique métier du jeu : comment on détermine
# quel Pokémon est avantagé face à un autre selon leurs types.
# C'est le cœur algorithmique du Battle Service, sans aucune dépendance externe.
# Il ne fait pas de I/O (pas de BDD, pas de réseau) → pur calcul Python.
# =============================================================================

# POURQUOI PAS D'IMPORT DE REDUCE ICI ?
# La formule utilise le produit des multiplicateurs, implémenté manuellement avec une boucle.
# C'est plus lisible et plus facile à expliquer à l'oral.

# Liste des 18 types Pokémon (génération 6+)
# Cette liste sert surtout de référence documentaire dans ce fichier
TYPES = [
    "Normal", "Feu", "Eau", "Plante", "Electrik", "Glace",
    "Combat", "Poison", "Sol", "Vol", "Psy", "Insecte",
    "Roche", "Spectre", "Dragon", "Tenebres", "Acier", "Fee"
]

# =============================================================================
# TYPE_CHART — Tableau des multiplicateurs de type
# =============================================================================
# Structure : TYPE_CHART[type_attaquant][type_défenseur] = multiplicateur
# Valeurs possibles :
#   2.0  = super efficace (attaque très forte)
#   1.0  = dégâts normaux
#   0.5  = pas très efficace (attaque affaiblie)
#   0    = immunité (aucun dégât)
#
# CHOIX DE DESIGN : données statiques hardcodées (pas en BDD)
# Raison : ce tableau est une donnée officielle Pokémon qui ne change jamais.
# Le mettre en BDD ajouterait une requête SQL inutile à chaque calcul de tour.
# C'est une constante de domaine, pas une donnée métier.
TYPE_CHART = {
    "Normal": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 1,
        "Roche": 0.5,    # Normal vs Roche = 0.5 (pas très efficace)
        "Spectre": 0,    # Normal vs Spectre = immunité !
        "Dragon": 1, "Tenebres": 1,
        "Acier": 0.5,    # Normal vs Acier = 0.5
        "Fee": 1
    },
    "Feu": {
        "Normal": 1,
        "Feu": 0.5,      # Feu vs Feu = résistance
        "Eau": 0.5,      # Feu vs Eau = résistance (l'eau éteint le feu)
        "Plante": 2,     # Feu vs Plante = super efficace
        "Electrik": 1,
        "Glace": 2,      # Feu vs Glace = super efficace
        "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1, "Psy": 1,
        "Insecte": 2,    # Feu vs Insecte = super efficace
        "Roche": 0.5,    # Feu vs Roche = résistance
        "Spectre": 1,
        "Dragon": 0.5,   # Feu vs Dragon = résistance
        "Tenebres": 1,
        "Acier": 2,      # Feu vs Acier = super efficace (fait fondre le métal)
        "Fee": 1
    },
    "Eau": {
        "Normal": 1, "Feu": 2, "Eau": 0.5, "Plante": 0.5, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 2, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 2, "Spectre": 1,
        "Dragon": 0.5, "Tenebres": 1, "Acier": 1, "Fee": 1
    },
    "Plante": {
        "Normal": 1, "Feu": 0.5, "Eau": 2, "Plante": 0.5, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 0.5, "Sol": 2, "Vol": 0.5,
        "Psy": 1, "Insecte": 0.5, "Roche": 2, "Spectre": 1,
        "Dragon": 0.5, "Tenebres": 1, "Acier": 0.5, "Fee": 1
    },
    "Electrik": {
        "Normal": 1, "Feu": 1,
        "Eau": 2,        # Electrik vs Eau = super efficace
        "Plante": 0.5, "Electrik": 0.5,
        "Glace": 1, "Combat": 1, "Poison": 1,
        "Sol": 0,        # Electrik vs Sol = immunité (la terre absorbe l'électricité)
        "Vol": 2,        # Electrik vs Vol = super efficace
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 0.5, "Tenebres": 1, "Acier": 1, "Fee": 1
    },
    "Glace": {
        "Normal": 1, "Feu": 0.5, "Eau": 0.5, "Plante": 2, "Electrik": 1,
        "Glace": 0.5, "Combat": 1, "Poison": 1, "Sol": 2, "Vol": 2,
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 2,     # Glace vs Dragon = super efficace (célèbre combo)
        "Tenebres": 1, "Acier": 0.5, "Fee": 1
    },
    "Combat": {
        "Normal": 2, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 2, "Combat": 1, "Poison": 0.5, "Sol": 1, "Vol": 0.5,
        "Psy": 0.5, "Insecte": 0.5, "Roche": 2,
        "Spectre": 0,    # Combat vs Spectre = immunité
        "Dragon": 1,
        "Tenebres": 2,   # Combat vs Ténèbres = super efficace
        "Acier": 2,
        "Fee": 0.5       # Combat vs Fée = pas très efficace
    },
    "Poison": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 2, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 0.5, "Sol": 0.5, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 0.5, "Spectre": 0.5,
        "Dragon": 1, "Tenebres": 1,
        "Acier": 0,      # Poison vs Acier = immunité
        "Fee": 2         # Poison vs Fée = super efficace
    },
    "Sol": {
        "Normal": 1, "Feu": 2, "Eau": 1, "Plante": 0.5,
        "Electrik": 2,   # Sol vs Electrik = super efficace (met à la terre)
        "Glace": 1, "Combat": 1, "Poison": 2, "Sol": 1,
        "Vol": 0,        # Sol vs Vol = immunité (les oiseaux volent au-dessus)
        "Psy": 1, "Insecte": 0.5, "Roche": 2, "Spectre": 1,
        "Dragon": 1, "Tenebres": 1, "Acier": 2, "Fee": 1
    },
    "Vol": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 2, "Electrik": 0.5,
        "Glace": 1,
        "Combat": 2,     # Vol vs Combat = super efficace
        "Poison": 1, "Sol": 1, "Vol": 1, "Psy": 1,
        "Insecte": 2,    # Vol vs Insecte = super efficace
        "Roche": 0.5, "Spectre": 1, "Dragon": 1, "Tenebres": 1,
        "Acier": 0.5, "Fee": 1
    },
    "Psy": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1,
        "Combat": 2,     # Psy vs Combat = super efficace
        "Poison": 2,     # Psy vs Poison = super efficace
        "Sol": 1, "Vol": 1, "Psy": 0.5, "Insecte": 1, "Roche": 1,
        "Spectre": 1, "Dragon": 1,
        "Tenebres": 0,   # Psy vs Ténèbres = immunité
        "Acier": 0.5, "Fee": 1
    },
    "Insecte": {
        "Normal": 1, "Feu": 0.5, "Eau": 1,
        "Plante": 2,     # Insecte vs Plante = super efficace
        "Electrik": 1, "Glace": 1, "Combat": 0.5, "Poison": 0.5,
        "Sol": 1, "Vol": 0.5,
        "Psy": 2,        # Insecte vs Psy = super efficace
        "Insecte": 1, "Roche": 1, "Spectre": 0.5, "Dragon": 1,
        "Tenebres": 2,   # Insecte vs Ténèbres = super efficace
        "Acier": 0.5, "Fee": 0.5
    },
    "Roche": {
        "Normal": 1,
        "Feu": 2,        # Roche vs Feu = super efficace
        "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 2,      # Roche vs Glace = super efficace
        "Combat": 0.5, "Poison": 1, "Sol": 0.5,
        "Vol": 2,        # Roche vs Vol = super efficace
        "Psy": 1,
        "Insecte": 2,    # Roche vs Insecte = super efficace
        "Roche": 1, "Spectre": 1, "Dragon": 1, "Tenebres": 1,
        "Acier": 0.5, "Fee": 1
    },
    "Spectre": {
        "Normal": 0,     # Spectre vs Normal = immunité
        "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1, "Glace": 1,
        "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 2,        # Spectre vs Psy = super efficace
        "Insecte": 1, "Roche": 1,
        "Spectre": 2,    # Spectre vs Spectre = super efficace
        "Dragon": 1,
        "Tenebres": 0.5, # Spectre vs Ténèbres = résistance
        "Acier": 1, "Fee": 1
    },
    "Dragon": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 2,     # Dragon vs Dragon = super efficace (duel de dragons)
        "Tenebres": 1,
        "Acier": 0.5,
        "Fee": 0         # Dragon vs Fée = immunité (les fées repoussent les dragons)
    },
    "Tenebres": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 0.5, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 2,        # Ténèbres vs Psy = super efficace
        "Insecte": 1, "Roche": 1,
        "Spectre": 2,    # Ténèbres vs Spectre = super efficace
        "Dragon": 1, "Tenebres": 0.5,
        "Acier": 1,
        "Fee": 0.5       # Ténèbres vs Fée = résistance
    },
    "Acier": {
        "Normal": 1,
        "Feu": 0.5,      # Acier vs Feu = résistance (le métal fond)
        "Eau": 0.5, "Plante": 1, "Electrik": 0.5,
        "Glace": 2,      # Acier vs Glace = super efficace (le métal brise la glace)
        "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1, "Psy": 1,
        "Insecte": 1,
        "Roche": 2,      # Acier vs Roche = super efficace
        "Spectre": 1, "Dragon": 1, "Tenebres": 1,
        "Acier": 0.5,
        "Fee": 2         # Acier vs Fée = super efficace
    },
    "Fee": {
        "Normal": 1,
        "Feu": 0.5,      # Fée vs Feu = résistance
        "Eau": 1, "Plante": 1, "Electrik": 1, "Glace": 1,
        "Combat": 2,     # Fée vs Combat = super efficace
        "Poison": 0.5,   # Fée vs Poison = résistance
        "Sol": 1, "Vol": 1, "Psy": 1, "Insecte": 1, "Roche": 1,
        "Spectre": 1,
        "Dragon": 2,     # Fée vs Dragon = super efficace (immunité du côté Dragon→Fée)
        "Tenebres": 2,   # Fée vs Ténèbres = super efficace
        "Acier": 0.5,    # Fée vs Acier = résistance
        "Fee": 1
    },
}


# =============================================================================
# FONCTION : get_multiplier — Récupère le multiplicateur entre deux types
# =============================================================================
def get_multiplier(atk: str, defense: str) -> float:
    # TYPE_CHART.get(atk) : récupère la ligne du type attaquant
    # Si le type n'est pas dans le tableau (type inconnu), on retourne 1.0 (neutre)
    row = TYPE_CHART.get(atk)
    if row is None:
        return 1.0  # Type inconnu = dégâts normaux par défaut
    # row.get(defense, 1.0) : récupère le multiplicateur contre le défenseur
    # Si le défenseur est inconnu → 1.0 par défaut
    return row.get(defense, 1.0)


# =============================================================================
# FONCTION : calc_advantage — Calcule F(A) et F(B)
# =============================================================================
# FORMULE MATHÉMATIQUE :
# F(A) = Σ(w ∈ types_A) [ Π(y ∈ types_B) get_multiplier(w, y) ]
#
# En français :
# Pour chaque type de A, on calcule le produit de ses multiplicateurs contre TOUS les types de B
# Puis on additionne ces produits pour tous les types de A
#
# Exemple : A = ["Feu", "Vol"], B = ["Plante", "Insecte"]
# F(A) = (Feu vs Plante × Feu vs Insecte) + (Vol vs Plante × Vol vs Insecte)
#      = (2 × 2) + (2 × 2) = 4 + 4 = 8.0
# F(B) = (Plante vs Feu × Plante vs Vol) + (Insecte vs Feu × Insecte vs Vol)
#      = (0.5 × 0.5) + (0.5 × 0.5) = 0.25 + 0.25 = 0.5
# → A gagne largement (8.0 vs 0.5)
def calc_advantage(types_a: list, types_b: list) -> tuple[float, float]:
    # Garde-fou : si une liste de types est vide, on retourne 0.0
    if not types_a or not types_b:
        return 0.0, 0.0

    # Calcul de F(A) : avantage de l'équipe A contre B
    fa = 0.0
    for w in types_a:           # Pour chaque type de A
        val = 1.0               # On commence avec un multiplicateur neutre
        for y in types_b:       # On multiplie par chaque type de B
            val *= get_multiplier(w, y)
        fa += val               # On additionne au score total de A

    # Calcul de F(B) : avantage de l'équipe B contre A (symétrique, rôles inversés)
    fb = 0.0
    for y in types_b:           # Pour chaque type de B
        val = 1.0
        for w in types_a:       # On multiplie par chaque type de A
            val *= get_multiplier(y, w)
        fb += val

    # round(..., 4) : arrondi à 4 décimales pour un affichage propre
    return round(fa, 4), round(fb, 4)


# =============================================================================
# FONCTION : resolve_turn — Détermine le vainqueur d'un tour
# =============================================================================
def resolve_turn(types_a: list, types_b: list) -> str:
    # On calcule les deux scores
    fa, fb = calc_advantage(types_a, types_b)
    
    if fa > fb:
        return "A"      # Équipe rouge (A) gagne ce tour
    if fb > fa:
        return "B"      # Équipe bleue (B) gagne ce tour
    return "draw"       # Égalité parfaite

# =============================================================================
# POURQUOI CE DESIGN ?
# =============================================================================
# 1. PURETÉ : ces fonctions n'ont aucun effet de bord (pas de BDD, pas de réseau)
#    → Faciles à tester unitairement
# 2. PERFORMANCE : calcul en O(types_A × types_B) = au max O(18×18) = O(324)
#    → Quasi-instantané
# 3. MAINTENABILITÉ : si les types changent (nouvelle génération Pokémon),
#    on modifie juste TYPE_CHART, pas la logique de calcul
