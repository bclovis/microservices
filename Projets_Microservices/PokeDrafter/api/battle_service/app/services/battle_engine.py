# TODO: optimiser ce dict, c'est un peu sale
# import random  # utilisé pour debug, à enlever plus tard

TYPES = [
    "Normal", "Feu", "Eau", "Plante", "Electrik", "Glace",
    "Combat", "Poison", "Sol", "Vol", "Psy", "Insecte",
    "Roche", "Spectre", "Dragon", "Tenebres", "Acier", "Fee"
]

# chaque ligne = type attaquant, chaque clé = type défenseur
TYPE_CHART = {
    "Normal": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 0.5, "Spectre": 0,
        "Dragon": 1, "Tenebres": 1, "Acier": 0.5, "Fee": 1
    },
    "Feu": {
        "Normal": 1, "Feu": 0.5, "Eau": 0.5, "Plante": 2, "Electrik": 1,
        "Glace": 2, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 2, "Roche": 0.5, "Spectre": 1,
        "Dragon": 0.5, "Tenebres": 1, "Acier": 2, "Fee": 1
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
        "Normal": 1, "Feu": 1, "Eau": 2, "Plante": 0.5, "Electrik": 0.5,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 0, "Vol": 2,
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 0.5, "Tenebres": 1, "Acier": 1, "Fee": 1
    },
    "Glace": {
        "Normal": 1, "Feu": 0.5, "Eau": 0.5, "Plante": 2, "Electrik": 1,
        "Glace": 0.5, "Combat": 1, "Poison": 1, "Sol": 2, "Vol": 2,
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 2, "Tenebres": 1, "Acier": 0.5, "Fee": 1
    },
    "Combat": {
        "Normal": 2, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 2, "Combat": 1, "Poison": 0.5, "Sol": 1, "Vol": 0.5,
        "Psy": 0.5, "Insecte": 0.5, "Roche": 2, "Spectre": 0,
        "Dragon": 1, "Tenebres": 2, "Acier": 2, "Fee": 0.5
    },
    "Poison": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 2, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 0.5, "Sol": 0.5, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 0.5, "Spectre": 0.5,
        "Dragon": 1, "Tenebres": 1, "Acier": 0, "Fee": 2
    },
    "Sol": {
        "Normal": 1, "Feu": 2, "Eau": 1, "Plante": 0.5, "Electrik": 2,
        "Glace": 1, "Combat": 1, "Poison": 2, "Sol": 1, "Vol": 0,
        "Psy": 1, "Insecte": 0.5, "Roche": 2, "Spectre": 1,
        "Dragon": 1, "Tenebres": 1, "Acier": 2, "Fee": 1
    },
    "Vol": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 2, "Electrik": 0.5,
        "Glace": 1, "Combat": 2, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 2, "Roche": 0.5, "Spectre": 1,
        "Dragon": 1, "Tenebres": 1, "Acier": 0.5, "Fee": 1
    },
    "Psy": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 2, "Poison": 2, "Sol": 1, "Vol": 1,
        "Psy": 0.5, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 1, "Tenebres": 0, "Acier": 0.5, "Fee": 1
    },
    "Insecte": {
        "Normal": 1, "Feu": 0.5, "Eau": 1, "Plante": 2, "Electrik": 1,
        "Glace": 1, "Combat": 0.5, "Poison": 0.5, "Sol": 1, "Vol": 0.5,
        "Psy": 2, "Insecte": 1, "Roche": 1, "Spectre": 0.5,
        "Dragon": 1, "Tenebres": 2, "Acier": 0.5, "Fee": 0.5
    },
    "Roche": {
        "Normal": 1, "Feu": 2, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 2, "Combat": 0.5, "Poison": 1, "Sol": 0.5, "Vol": 2,
        "Psy": 1, "Insecte": 2, "Roche": 1, "Spectre": 1,
        "Dragon": 1, "Tenebres": 1, "Acier": 0.5, "Fee": 1
    },
    "Spectre": {
        "Normal": 0, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 2, "Insecte": 1, "Roche": 1, "Spectre": 2,
        "Dragon": 1, "Tenebres": 0.5, "Acier": 1, "Fee": 1
    },
    "Dragon": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 2, "Tenebres": 1, "Acier": 0.5, "Fee": 0
    },
    "Tenebres": {
        "Normal": 1, "Feu": 1, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 0.5, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 2, "Insecte": 1, "Roche": 1, "Spectre": 2,
        "Dragon": 1, "Tenebres": 0.5, "Acier": 1, "Fee": 0.5
    },
    "Acier": {
        "Normal": 1, "Feu": 0.5, "Eau": 0.5, "Plante": 1, "Electrik": 0.5,
        "Glace": 2, "Combat": 1, "Poison": 1, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 2, "Spectre": 1,
        "Dragon": 1, "Tenebres": 1, "Acier": 0.5, "Fee": 2
    },
    "Fee": {
        "Normal": 1, "Feu": 0.5, "Eau": 1, "Plante": 1, "Electrik": 1,
        "Glace": 1, "Combat": 2, "Poison": 0.5, "Sol": 1, "Vol": 1,
        "Psy": 1, "Insecte": 1, "Roche": 1, "Spectre": 1,
        "Dragon": 2, "Tenebres": 2, "Acier": 0.5, "Fee": 1
    },
}


def get_multiplier(atk, defense):
    row = TYPE_CHART.get(atk)
    if row is None:
        return 1.0
    return row.get(defense, 1.0)


# F(A) = somme sur chaque type de A du produit des multis contre chaque type de B
# si le pokemon est monotype on considère qu'il a deux fois le même type
def calc_advantage(types_a, types_b):
    if not types_a or not types_b:
        return 0.0, 0.0

    ta = types_a if len(types_a) == 2 else [types_a[0], types_a[0]]
    tb = types_b if len(types_b) == 2 else [types_b[0], types_b[0]]

    fa = 0.0
    for w in ta:
        val = 1.0
        for y in tb:
            val *= get_multiplier(w, y)
        fa += val

    fb = 0.0
    for y in tb:
        val = 1.0
        for w in ta:
            val *= get_multiplier(y, w)
        fb += val

    return round(fa, 4), round(fb, 4)


def resolve_turn(types_a, types_b):
    fa, fb = calc_advantage(types_a, types_b)
    if fa > fb:
        return "A"
    if fb > fa:
        return "B"
    return "draw"
