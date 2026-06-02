# Fiche — Structure du `config.json`

---

## Structure de la conf

### `project`
Infos générales du script : nom, environnement (`preprod` / `prod`), chemin du fichier de log.

### `connection`
Liste des connexions disponibles (Impala via DSN ODBC, SMTP).
Chaque connexion a un `name` — c'est ce nom qu'on référence dans les abonnements.

### `monitoringEventsTable`
Nom de la table à interroger : `interne_data.monitoring_events`.
Un seul endroit à changer si la table change de nom.

### `subscriptions`
Liste des abonnements. Chaque abonnement = 1 mail potentiel à chaque exécution.

| Clé | Description |
|---|---|
| `name` | Identifiant de l'abonnement (pour les logs) |
| `description` | Explication lisible de ce que fait l'abonnement |
| `isActive` | `true` = actif, `false` = ignoré sans toucher au code |
| `connexionName` | Nom de la connexion Impala à utiliser |
| `filters` | Filtres utilisés pour construire la requête SQL |
| `email` | Destinataires, sujet, connexion SMTP |

#### Filtres disponibles dans un abonnement

| Filtre | Type | Description |
|---|---|---|
| `criticality` | `tous` / `alerte+critique` / `critique` | Filtre sur le champ `status` |
| `deltaHours` | entier | Ne regarder que les N dernières heures (`process_date`) |
| `source` | string | Ex : `ouigos3dfr_global` |
| `source_detail` | string | Ex : `caiman_export_dossier` |
| `source_type` | string | Ex : `iceberg` |
| `rule_category` | string | Ex : `data_quality`, `anomaly_detection`, `consistency` |
| `rule` | string | Ex : `nbr_hard_error_variation`, `missing_chunks` |

Tous les filtres sont optionnels et cumulables (ET logique). Filtre absent = pas de condition sur cette colonne.

---

## SQL généré derrière

Le code construit dynamiquement un `WHERE` à partir des filtres de l'abonnement.
Le `SELECT` est toujours le même — toutes les colonnes de `monitoring_events`.

**Exemple — abonnement `exemple_missing_chunks_ouigos3dfr`** :

```json
"filters": {
  "source": "ouigos3dfr_global",
  "rule_category": "consistency",
  "rule": "missing_chunks",
  "criticality": "alerte+critique",
  "deltaHours": 24
}
```

→ SQL généré :

```sql
SELECT source, source_detail, source_type, rule_category, rule,
       process_date, metric_name, metric_value, threshold_value, status, message
FROM interne_data.monitoring_events
WHERE process_date >= now() - interval 24 hours
  AND status IN ('ALERTE', 'CRITIQUE')
  AND source = 'ouigos3dfr_global'
  AND rule_category = 'consistency'
  AND rule = 'missing_chunks'
ORDER BY status DESC, source, process_date DESC
```

> Les résultats sont déjà calculés par d'autres process et stockés dans la table.
> Ce script ne recalcule rien — il lit, filtre, et envoie le mail si des lignes remontent.

---

## Question ouverte — autres clients, autres tables ?

**Aujourd'hui** : une seule table `interne_data.monitoring_events`, tous les abonnements tapent la même base (`impala_ouigos3dfr`).

**Si demain un autre client a sa propre BDD** avec sa propre table `monitoring_events` :
→ ajouter une connexion dans `connection` + référencer ce nom dans `connexionName` de l'abonnement.
→ Le script gère déjà plusieurs connexions en parallèle (pool de connexions).

**Si tous les clients partagent la même table** :
→ la colonne `source` sert à les distinguer — un abonnement par client avec `"source": "nom_du_client"`.
→ Dans ce cas tous les abonnements auront le même `connexionName`, et la connexion `impala_autre_client` dans la conf actuelle n'a pas de raison d'être.

**À valider avec Christophe** : est-ce que `monitoring_events` est une table commune à tous les clients ou est-ce que chaque client aura la sienne ?
