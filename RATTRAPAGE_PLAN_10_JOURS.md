# GenericMonitoring — Documentation complète

## Table des matières
1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Structure des fichiers](#3-structure-des-fichiers)
4. [config.json — La configuration](#4-configjson--la-configuration)
5. [main.py — L'orchestrateur](#5-mainpy--lorchéstrateur)
6. [monitor_utils.py — La logique métier](#6-monitor_utilspy--la-logique-métier)
7. [email_template.py — Les emails HTML](#7-email_templatepy--les-emails-html)
8. [smtp_mailer.py — L'envoi email](#8-smtp_mailerpy--lenvoi-email)
9. [Ajouter un abonnement](#9-ajouter-un-abonnement)
10. [Cas d'usage concrets](#10-cas-dusage-concrets)
11. [Déploiement](#11-déploiement)

---

## 1. Vue d'ensemble

**GenericMonitoring** est un script Python qui surveille le contenu de la table Impala `interne_data.monitoring_events` et envoie des alertes par email quand des événements correspondent aux critères configurés.

### Principe
D'autres processus (jobs de profiling, scripts de surveillance, etc.) écrivent des événements dans `monitoring_events`. GenericMonitoring lit cette table, filtre selon des abonnements configurés, et notifie les équipes par email.

### Ce que le script fait à chaque exécution
1. Charge `config.json`
2. Pour chaque abonnement actif : exécute un SELECT sur `monitoring_events`
3. Si des événements sont trouvés → envoie un email d'alerte HTML
4. Si une erreur technique survient → envoie un email d'erreur
5. Logue les métriques dans LDMLog (SQL Server)

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  PRODUCTEURS                                                  │
│                                                              │
│  IcebergMonitoring ──┐                                       │
│  ProfilingJob      ──┼──► interne_data.monitoring_events     │
│  ChunksJob         ──┘         (table Impala)                │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  GenericMonitoring (ce script)                               │
│                                                              │
│  config.json ──► abonnements ──► SELECT sur monitoring_events│
│                                        │                     │
│                               0 ligne  │  N lignes           │
│                               rien     ▼  email HTML         │
└──────────────────────────────────────────────────────────────┘
```

### Modèle pub/sub
- **Producteurs** : écrivent dans `monitoring_events` sans savoir qui lira
- **Consommateur** : GenericMonitoring lit et filtre selon les abonnements
- **Avantage** : pour ajouter un nouveau cas d'usage, il suffit d'écrire dans `monitoring_events`. Aucune modification du code GenericMonitoring.

---

## 3. Structure des fichiers

```
GenericMonitoring/
└── src/
    ├── main.py                  ← orchestrateur principal (que main())
    ├── config/
    │   └── config.json          ← abonnements, connexions, destinataires
    ├── mail/
    │   ├── smtp_mailer.py       ← envoi mail HTML/texte via SMTP
    │   └── email_template.py    ← rendu HTML des mails d'alerte et d'erreur
    └── utils/
        └── monitor_utils.py     ← connexions, build_query, run_subscription,
                                    send_error_email, log_to_ldmlog
```

---

## 4. config.json — La configuration

Tout ce que le script sait faire est dans ce fichier. **Aucune modification de code n'est nécessaire** pour ajouter un abonnement.

### Section `project`
```json
"project": {
  "projectName": "Generic Monitoring",
  "processName": "monitoring_events Subscription Alerting",
  "environment": "prod",
  "logPath": "D:\\Data\\Cyllene\\GenericMonitoring\\Data\\Log\\generic_monitoring.log"
}
```
- `environment` : affiché dans les emails (`prod` ou `preprod`)
- `logPath` : chemin du fichier de log (le dossier est créé automatiquement)

### Section `connection`
Liste de toutes les connexions utilisées dans le script.

```json
"connection": [
  {
    "name": "impala_ouigos3dfr",
    "protocol": "odbc",
    "dsn": "ouigos3dfr_preprod_impala"       ← DSN Windows ODBC
  },
  {
    "name": "ldmlog",
    "driver": "ODBC Driver 17 for SQL Server",
    "server": "SRVSQL-PROD",
    "database": "LDMLog",
    "trustedConnection": true                 ← authentification Windows
  },
  {
    "name": "ldm_smtp",
    "protocol": "tls",
    "server": "dagobah.leadeal-marketing.local",
    "port": 25                                ← pas d'authentification
  }
]
```

### Section `monitoringEventsTable`
```json
"monitoringEventsTable": "interne_data.monitoring_events"
```
Nom de la table Impala surveillée. Utilisé dans tous les SELECT.

### Section `subscriptions`
C'est le cœur de la configuration. Chaque abonnement définit quoi surveiller et à qui envoyer.

```json
{
  "name": "alerte_global_cyllene",         ← identifiant unique (apparaît dans les logs)
  "description": "...",                     ← optionnel, pour la doc
  "isActive": true,                         ← false = ignoré complètement
  "connexionName": "impala_ouigos3dfr",     ← quelle connexion Impala utiliser
  "filters": {                              ← conditions du WHERE
    "status": ["ALERTE", "CRITIQUE"],
    "deltaHours": 24
  },
  "maxRows": 500,                           ← optionnel, défaut 500 (LIMIT dans le SQL)
  "email": {
    "connexionName": "ldm_smtp",
    "subject": "[GenericMonitoring][ALERTE] ...",
    "from": "LDM-IT-Exploitation@leadeal-marketing.com",
    "to": ["cyllene-data-exploitation@groupe-cyllene.com"],
    "cc": []
  }
}
```

### Filtres disponibles

| Clé | Type | SQL généré | Exemple |
|-----|------|-----------|---------|
| `status` | liste ou string | `status IN ('ALERTE','CRITIQUE')` ou `status = 'CRITIQUE'` | `["ALERTE","CRITIQUE"]` |
| `deltaHours` | int | `process_date >= now() - interval N hours` | `24` |
| `source` | string | `source = 'valeur'` | `"ouigos3dfr_global"` |
| `source_detail` | string | `source_detail = 'valeur'` | `"ouigos3dfr_global.ticket_booking"` |
| `source_type` | string | `source_type = 'valeur'` | `"iceberg"` |
| `rule_category` | string | `rule_category = 'valeur'` | `"anomaly_detection"` |
| `rule` | string | `rule = 'valeur'` | `"nbr_hard_error_variation"` |

Tous les filtres sont **optionnels**. Si aucun filtre → toute la table est interrogée (warning dans le log).

### Section `errorEmail`
Email envoyé uniquement en cas d'erreur technique (SQL plante, SMTP down, etc.). **Pas envoyé** si tout s'est bien passé.

```json
"errorEmail": {
  "connexionName": "ldm_smtp",
  "subject": "[GenericMonitoring][ERROR] Erreur technique",
  "from": "LDM-IT-Exploitation@leadeal-marketing.com",
  "to": ["cyllene-data-exploitation@groupe-cyllene.com"],
  "cc": []
}
```

### Section `ldmlog`
Paramètres pour l'insertion dans LDMLog (SQL Server) à chaque exécution.

```json
"ldmlog": {
  "customerCode": "LDM",
  "projectCode": "GenericMonitoring",
  "processType": "Monitoring",
  "applicationName": "GenericMonitoring",
  "storedProcedure": "[TraitementLog].[PS_CollecteLogTraitement]"
}
```

---

## 5. main.py — L'orchestrateur

**Rôle** : chef d'orchestre. Ne contient que `main()`. Toute la logique métier est dans `monitor_utils.py`.

### Flux complet

```python
def main():
    startedAt = datetime.now()          # 1. Heure de début (pour LDMLog et durée)

    # 2. Argument --config optionnel (permet de passer un config alternatif)
    #    python src\main.py --config autre_config.json
    configPath = args.config or "src/config/config.json"

    # 3. Chargement du config.json
    #    Si le fichier n'existe pas ou est invalide → print + return (arrêt propre)
    config = json.load(configPath)

    # 4. Activation du logger (fichier log, UTF-8, crée le dossier si besoin)
    configure_logging(config['project']['logPath'])

    # 5. Filtre les abonnements actifs (isActive = true)
    activeSubscriptions = [s for s in config['subscriptions'] if s['isActive']]

    # 6. Connexions Impala partagées entre abonnements
    #    get_or_open_conn() ouvre une connexion la 1ère fois, la réutilise ensuite
    #    → 2 abonnements sur le même DSN = 1 seule connexion Impala

    # 7. Boucle principale
    for sub in activeSubscriptions:
        try:
            results.append(run_subscription(sub, conn, eventsTable, config))
        except Exception as e:
            errors.append(...)    # erreur enregistrée, on continue les autres

    # 8. Mail d'erreur UNIQUEMENT si erreurs techniques
    if errors:
        send_error_email(results, errors, startedAt, endedAt, config)

    # 9. LDMLog — toujours, même si erreurs
    #    Si SRVSQL-PROD injoignable → loggué et ignoré, script finit normalement
    log_to_ldmlog(...)
```

### Comportement en cas d'erreur
- **Config invalide** → arrêt immédiat (print, pas de log)
- **Subscription qui plante** → les autres continuent, erreur enregistrée
- **LDMLog injoignable** → loggué, script finit normalement
- **SMTP down** → erreur loggée, subscription marquée en erreur

---

## 6. monitor_utils.py — La logique métier

### `get_connection_cfg(config, name)`
Cherche une connexion par son nom dans `config['connection']`.
```python
smtpCfg = get_connection_cfg(config, "ldm_smtp")
# → {"name": "ldm_smtp", "server": "dagobah...", "port": 25}
```
Lève `ValueError` si le nom n'existe pas.

---

### `get_impala_connection(dsnName)`
Ouvre une connexion ODBC Impala via le DSN Windows.
```python
conn = get_impala_connection("ouigos3dfr_preprod_impala")
# → connexion pyodbc prête à exécuter des SELECT
```

---

### `connect_sql_server(connName, config)`
Ouvre une connexion SQL Server pour LDMLog (authentification Windows `Trusted_Connection`).
```python
connLdmlog = connect_sql_server("ldmlog", config)
```

---

### `configure_logging(logPath)`
Active le logger Python vers un fichier.
- Crée le dossier automatiquement si besoin
- Format : `2026-06-05 09:15:33,598 INFO [main] Generic Monitoring started`
- Encodage UTF-8

---

### `build_query(table, filters, maxRows=500)`
Construit le SQL dynamiquement depuis les filtres de l'abonnement.

```python
build_query(
    "interne_data.monitoring_events",
    {"status": ["ALERTE", "CRITIQUE"], "deltaHours": 24, "source": "ouigos3dfr_global"},
    500
)
```
Génère :
```sql
SELECT source, source_detail, source_type, rule_category, rule,
       process_date, metric_name, metric_value, threshold_value, status, message
FROM interne_data.monitoring_events
WHERE process_date >= now() - interval 24 hours
  AND status IN ('ALERTE', 'CRITIQUE')
  AND source = 'ouigos3dfr_global'
ORDER BY status DESC, source, process_date DESC
LIMIT 500
```

**Détail de la construction :**
1. `deltaHours` → condition sur `process_date`
2. `status` liste → `IN (...)` / string → `= '...'`
3. `source`, `source_detail`, `source_type`, `rule_category`, `rule` → `col = 'valeur'` si présent
4. Assemblage avec `AND`
5. `LIMIT maxRows` toujours présent (garde-fou anti surcharge)

---

### `run_subscription(sub, conn, eventsTable, config)`
Traite un abonnement de A à Z.

```
1. Récupère les filtres et maxRows de l'abonnement
2. Warning si aucun filtre (toute la table sera interrogée)
3. build_query() → SQL
4. cursor.execute(sql) + fetchall()
   → erreur SQL → raise (main() attrape et continue)
5. 0 ligne → return {"eventsFound": 0, "emailSent": False}
6. N lignes :
   → render_alert_email() → HTML
   → send_email()
   → return {"eventsFound": N, "emailSent": True}
```

Retourne toujours un dict `{"subscription": nom, "eventsFound": N, "emailSent": bool}`.

---

### `send_error_email(results, errors, startedAt, endedAt, config)`
Envoie le mail de rapport d'erreur technique.
- Appelé **uniquement** si `errors` est non vide
- Contenu : tableau récap des abonnements + détail des erreurs

---

### `log_to_ldmlog(connLdmlog, config, startedAt, endedAt, stats)`
Appelle la procédure stockée `[TraitementLog].[PS_CollecteLogTraitement]` avec 20 paramètres :
- Codes projet/client/process
- Dates de début et fin
- Nombre de records traités, succès, erreurs
- Nom de la machine (`socket.gethostname()`)
- Message d'erreur si applicable

---

## 7. email_template.py — Les emails HTML

### `render_alert_email(rows, events_table, environment)`
Génère le mail envoyé quand des événements sont trouvés.

**Contenu :**
- Header bleu foncé avec "Alerte Monitoring — événements détectés"
- Intro : "X événement(s) correspondant aux critères de votre abonnement"
- Tableau HTML avec 11 colonnes : source, détail source, type source, catégorie règle, règle, date traitement, métrique, valeur, seuil, **statut (badge coloré)**, message
- Footer avec environnement et date

**Couleurs des badges statut :**
- `CRITIQUE` → rouge `#c0392b`
- `ALERTE` → orange `#e67e22`
- Autre → gris `#888`

---

### `render_error_email(results, errors, startedAt, endedAt, environment)`
Génère le mail de rapport d'erreur technique.

**Contenu :**
- Header rouge (si erreurs) ou vert (si OK)
- Ligne de métriques : X subscriptions, Y événements, Z mails, N erreurs
- Tableau par abonnement : nom | events trouvés | mail envoyé (✓ ou —)
- Section erreurs techniques si applicable

---

## 8. smtp_mailer.py — L'envoi email

```python
send_email(
    smtpServer="dagobah.leadeal-marketing.local",
    smtpPort=25,
    smtpUserName="",        # vide = pas d'authentification
    smtpPassword="",
    emailSubject="...",
    emailMessage=body_html,
    emailFrom="LDM-IT-Exploitation@...",
    emailTo=["destinataire@..."],
    emailCc=[],
    is_html=True
)
```

**Logique de connexion SMTP :**
- Port 465 → `SMTP_SSL`
- Port 25/587 → `SMTP` + `STARTTLS` si disponible (silencieux si non)
- Auth si `smtpUserName` non vide, sinon pas d'auth (notre cas avec `dagobah`)

---

## 9. Ajouter un abonnement

**Aucune modification de code.** Uniquement dans `config.json`, section `subscriptions`.

### Template complet
```json
{
  "name": "nom_unique_abonnement",
  "description": "Description lisible de ce que surveille cet abonnement",
  "isActive": true,
  "connexionName": "impala_ouigos3dfr",
  "filters": {
    "status": ["ALERTE", "CRITIQUE"],
    "deltaHours": 24,
    "source": "nom_source",
    "rule_category": "categorie_regle",
    "rule": "nom_regle"
  },
  "maxRows": 500,
  "email": {
    "connexionName": "ldm_smtp",
    "subject": "[GenericMonitoring][ALERTE] Description courte",
    "from": "LDM-IT-Exploitation@leadeal-marketing.com",
    "to": ["destinataire@groupe-cyllene.com"],
    "cc": []
  }
}
```

### Désactiver temporairement
```json
"isActive": false
```
L'abonnement est ignoré, aucun email envoyé, aucune requête exécutée.

### Exemple : surveillance chunks manquants
```json
{
  "name": "alerte_missing_chunks_ouigos3dfr",
  "isActive": true,
  "connexionName": "impala_ouigos3dfr",
  "filters": {
    "source": "ouigos3dfr_global",
    "rule_category": "consistency",
    "rule": "missing_chunks",
    "status": ["ALERTE", "CRITIQUE"],
    "deltaHours": 24
  },
  "email": {
    "connexionName": "ldm_smtp",
    "subject": "[GenericMonitoring][ALERTE] Chunks manquants OuigoS3DFR",
    "from": "LDM-IT-Exploitation@leadeal-marketing.com",
    "to": ["OuigoS3DataFR-exploitation@groupe-cyllene.com"],
    "cc": []
  }
}
```

---

## 10. Cas d'usage concrets

### Cas 1 — Surveillance anomalies (`nbr_hard_error`)
Un job de profiling calcule quotidiennement le nombre d'erreurs par table Iceberg. Si la variation est anormale, il écrit dans `monitoring_events` :
```
source          = "ouigos3dfr_crm"
rule_category   = "data_quality"
rule            = "nbr_hard_error_variation"
metric_value    = 20468    (nouvelles erreurs)
threshold_value = 12884    (seuil)
status          = "ALERTE"
message         = "+58% vs seuil"
```
L'abonnement `alerte_global_cyllene` le détecte et envoie l'email. ✅ **Testé en conditions réelles.**

### Cas 2 — Surveillance chunks manquants
Un job SQL compare le référentiel aux tables existantes → calcule le nombre de chunks manquants par table et par date → si dépasse seuil → écrit dans `monitoring_events` avec `rule_category = 'consistency'` et `rule = 'missing_chunks'`. L'abonnement correspondant (actuellement `isActive: false`) détecte et alerte.

### Cas 3 — Surveillance fraîcheur de `monitoring_events` elle-même
**Géré par Iceberg Monitoring** (script indépendant) et non par GenericMonitoring — pour éviter la dépendance circulaire ("qui surveille le surveillant ?"). Iceberg Monitoring vérifie `MAX(process_date)` de `monitoring_events` indépendamment.

---

## 11. Déploiement

### Lancement manuel
```
run.bat  →  python src\main.py
```
Ou directement :
```
python src\main.py
python src\main.py --config chemin\vers\autre_config.json
```

### Sur Sidious (production)
| Élément | Chemin |
|---------|--------|
| Script | `D:\Data\Cyllene\GenericMonitoring\Script\` |
| Log | `D:\Data\Cyllene\GenericMonitoring\Data\Log\generic_monitoring.log` |

### Déploiement via GitLab CI/CD
Repo : `https://gitlab.leadeal-marketing.local/script/cyllene/genericmonitoring`

Pipeline `.gitlab-ci.yml` → job `deploy_prod` → déclenchement **manuel** depuis GitLab → copie les fichiers sur Sidious via SCP.

Variable GitLab requise : `$msqluser_password` (Settings → CI/CD → Variables)

### Cron Airflow
À configurer pour exécuter `run.bat` à la fréquence souhaitée (ex: toutes les heures).

### Prérequis sur le serveur
- Python 3.10+
- `pip install pyodbc`
- DSN Windows ODBC `ouigos3dfr_preprod_impala` configuré
- Accès réseau à `dagobah.leadeal-marketing.local:25` (SMTP)
- Accès réseau à `SRVSQL-PROD` (LDMLog)
- Compte de service avec `SELECT` sur `interne_data.monitoring_events`
