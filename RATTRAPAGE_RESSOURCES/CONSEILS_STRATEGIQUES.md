# Generic Monitoring — KMN-93

Script de surveillance et d'alerting générique basé sur la table d'événements `interne_data.monitoring_events`.

---

## Contexte

Le script [KMN-61](https://jira-cyllene.atlassian.net/browse/KMN-61) surveille la fraîcheur de tables Iceberg : il fait un `MAX()` sur une colonne de date et envoie un mail si le retard dépasse un seuil. Il ne sait faire que ça.

**KMN-93** généralise la surveillance : d'autres process du datalake calculent déjà des règles métier (taux d'erreurs, anomalies, volumétrie…) et écrivent leurs résultats dans une table centrale `interne_data.monitoring_events`. Ce script lit cette table et notifie les bonnes équipes selon des abonnements configurables.

---

## Architecture

```
Process métier A  ──┐
Process métier B  ──┼──► interne_data.monitoring_events ◄── GenericMonitoring ──► Mails
Process métier C  ──┘
```

Le script ne calcule pas les règles — elles sont déjà calculées et stockées. Il fait **lire → filtrer → notifier**.

---

## Structure de la table `monitoring_events`

| Colonne | Type | Description |
|---|---|---|
| `source` | string | Source de l'événement (ex: `ouigos3dfr_crm`) |
| `source_detail` | string | Détail de la source (ex: `actionable_export_booking`) |
| `source_type` | string | Type de source (ex: `iceberg`) |
| `rule_category` | string | Catégorie de la règle (ex: `data_quality`) |
| `rule` | string | Nom de la règle (ex: `nbr_hard_error_variation`) |
| `process_date` | timestamp | Date de traitement de la donnée source |
| `metric_name` | string | Nom de la métrique (ex: `delta_error`) |
| `metric_value` | double | Valeur observée |
| `threshold_value` | double | Valeur de seuil |
| `status` | string | `OK` / `ALERTE` / `CRITIQUE` |
| `message` | string | Explication si statut != OK |
| `event_creation_date` | timestamp | Date d'insertion de l'événement |
| `event_modification_date` | timestamp | Date de dernière mise à jour de l'événement |

---

## Fonctionnement

À chaque exécution, pour chaque abonnement actif :

1. Connexion Impala via DSN ODBC
2. Construction du SQL selon les filtres de l'abonnement
3. Exécution sur `monitoring_events`
4. Si des lignes remontent → mail HTML avec tableau des événements
5. Si aucune ligne → rien (log info)
6. Si erreur technique → mail d'erreur à l'équipe tech

### Exemple de SQL généré

```sql
SELECT source, source_detail, source_type, rule_category, rule,
       process_date, metric_name, metric_value, threshold_value,
       status, message, event_creation_date, event_modification_date
FROM interne_data.monitoring_events
WHERE process_date >= now() - interval 24 hours
  AND status IN ('ALERTE', 'CRITIQUE')
ORDER BY status DESC, source, process_date DESC
```

---

## Configuration

Tout est dans [`src/config/config.json`](src/config/config.json) — aucun code à modifier pour ajouter un abonnement.

### Exemple complet de `config.json`

```json
{
  "project": {
    "projectName": "Generic Monitoring",
    "processName": "monitoring_events Subscription Alerting",
    "environment": "preprod",
    "logPath": "C:\\chemin\\vers\\logs\\generic_monitoring.log"
  },

  // ─── Connexions disponibles ───────────────────────────────────────────────
  "connection": [
    {
      "name": "impala_ouigos3dfr",   // nom utilisé dans les abonnements
      "protocol": "odbc",
      "dsn": "ouigos3dfr_preprod_impala"  // nom du DSN ODBC Windows
    },
    {
      "name": "ldm_smtp",
      "protocol": "tls",
      "server": "dagobah.leadeal-marketing.local",
      "port": 25
    }
  ],

  // ─── Table centrale des événements ───────────────────────────────────────
  "monitoringEventsTable": "interne_data.monitoring_events",

  // ─── Abonnements — chaque bloc = 1 mail envoyé selon des filtres ──────────
  "subscriptions": [
    {
      "name": "alerte_global_cyllene",
      "description": "Tous les ALERTE/CRITIQUE du datalake → équipe exploitation Cyllene",
      "isActive": true,
      "connexionName": "impala_ouigos3dfr",  // quelle BDD interroger
      "filters": {
        "source": null,            // null = toutes les sources sans restriction
        "criticality": "alerte+critique",  // "tous" | "alerte+critique" | "critique"
        "deltaHours": 24           // ne regarder que les 24 dernières heures
      },
      "email": {
        "connexionName": "ldm_smtp",
        "subject": "[ALERTE] Monitoring événements datalake",
        "from": "LDM-IT-Exploitation@leadeal-marketing.com",
        "to": ["cyllene-data-exploitation@groupe-cyllene.com"],
        "cc": []
      }
    },
    {
      "name": "alerte_ouigos3dfr_critique_seulement",
      "description": "Uniquement les CRITIQUE OuigoS3DFR → équipe Ouigo + chef de projet",
      "isActive": true,
      "connexionName": "impala_ouigos3dfr",
      "filters": {
        "source": "ouigos3dfr_crm",  // filtrer sur une source précise
        "criticality": "critique",   // uniquement les CRITIQUE
        "deltaHours": 6              // fenêtre plus courte : 6h
      },
      "email": {
        "connexionName": "ldm_smtp",
        "subject": "[CRITIQUE] Monitoring OuigoS3DFR CRM",
        "from": "LDM-IT-Exploitation@leadeal-marketing.com",
        "to": ["OuigoS3DataFR-exploitation@groupe-cyllene.com"],
        "cc": ["chef-de-projet@exemple.com"]
      }
    }
  ],

  // ─── Mail envoyé en cas d'erreur technique du script lui-même ─────────────
  "errorEmail": {
    "connexionName": "ldm_smtp",
    "subject": "[ERROR] Erreur technique - Generic Monitoring",
    "from": "LDM-IT-Exploitation@leadeal-marketing.com",
    "to": ["cyllene-data-exploitation@groupe-cyllene.com"],
    "cc": []
  }
}
```

> **Note** : JSON ne supporte pas les commentaires `//` — les lignes ci-dessus sont uniquement pour la lisibilité de cette doc. Le vrai fichier n'en contient pas.

### Abonnements configurés

| Nom | Source | Criticité | Fenêtre | Destinataires |
|---|---|---|---|---|
| `alerte_global_cyllene` | toutes | ALERTE + CRITIQUE | 24h | cyllene-data-exploitation@ |
| `alerte_ouigos3dfr_global` | `ouigos3dfr_global` | ALERTE + CRITIQUE | 24h | OuigoS3DataFR-exploitation@ |

### Ajouter un abonnement

Ajouter un bloc dans la section `subscriptions` de `config.json` :

```json
{
  "name": "alerte_nouveau_client",
  "isActive": true,
  "connexionName": "impala_ouigos3dfr",
  "filters": {
    "source": "nouveau_client",
    "criticality": "alerte+critique",
    "deltaHours": 24
  },
  "email": {
    "connexionName": "ldm_smtp",
    "subject": "[ALERTE] Monitoring nouveau client",
    "from": "LDM-IT-Exploitation@leadeal-marketing.com",
    "to": ["equipe@groupe-cyllene.com"],
    "cc": []
  }
}
```

Valeurs possibles pour `criticality` : `tous` / `alerte+critique` / `critique`

### Ajouter une connexion BDD

```json
{
  "name": "impala_nouveau_client",
  "protocol": "odbc",
  "dsn": "nouveau_client_preprod_impala"
}
```

Puis référencer ce nom dans `connexionName` de l'abonnement.

---

## Structure des fichiers

```
GenericMonitoring/
├── README.md
└── src/
    ├── main.py                  ← orchestrateur principal
    ├── config/
    │   └── config.json          ← abonnements, connexions, destinataires
    ├── mail/
    │   └── smtp_mailer.py       ← envoi mail HTML/texte via SMTP
    └── utils/
        └── monitor_utils.py     ← connexion Impala, logging, mail d'erreur
```

---

## Surveillance de `monitoring_events` elle-même

La fraîcheur de la table `monitoring_events` est surveillée par le script KMN-61 (iceberg-monitoring).
Une tâche a été ajoutée dans sa config :

```json
{
  "name": "monitor_monitoring_eve_freshness",
  "flux": {
    "sourceTable": "interne_data.monitoring_events",
    "dateColumn": "process_date",
    "threshold_minutes": 1
  }
}
```

Si la table n'est plus alimentée → mail d'alerte KMN-61.

---

## Prérequis

- Python 3.10+
- `pyodbc`
- DSN ODBC Cloudera Impala configuré sur la machine
- Accès réseau au serveur SMTP `dagobah.leadeal-marketing.local`
- Droits `SELECT` sur `interne_data.monitoring_events`

---

## Lancement

```bash
python src/main.py
# ou avec un config alternatif
python src/main.py --config /chemin/vers/config.json
```

---

## Ce qui reste à faire

- [ ] Droits SELECT sur `interne_data.monitoring_events` pour le compte de service
- [ ] Remplacer les adresses mail de test par les vraies adresses de prod
- [ ] Valider avec Christophe qu'un vrai ALERTE déclenche le bon mail
- [ ] Configurer le cron Airflow
- [ ] Compléter la [doc Wiki](https://wiki.groupe-cyllene.com/books/kamino-fonctionnelle/page/monitoring-devenements)
