KMN-93 — Généralisation du monitoring
Explication complète de la solution
02/06/2026


LE PROBLEME DE DEPART
---------------------

On avait déjà un script (KMN-61) qui surveillait la fraîcheur de tables Iceberg chez Ouigo.
Son principe : pour chaque table configurée, il fait un MAX() sur une colonne de date, compare
à l'heure actuelle, et envoie un mail d'alerte si le retard dépasse un seuil en minutes.

Ce script fonctionne bien, mais il est limité : il ne sait faire que ce contrôle-là.
Si demain on veut surveiller un taux d'erreurs ou un nombre d'anomalies, il faut modifier
le code Python. Ce n'est pas maintenable sur le long terme.

Le besoin exprimé dans KMN-93 : généraliser ce système pour pouvoir surveiller
n'importe quelle métrique, sans toucher au code à chaque nouveau cas d'usage.


COMMENT ON A TROUVE LA SOLUTION
--------------------------------

En discutant avec Christophe et Sofiane, deux cas d'usage concrets ont émergé :
1. Surveiller le taux d'erreurs dures dans le profiling Ouigo (nbr_hard_error / nbr_rows)
2. Détecter une croissance anormale du nombre d'anomalies d'un jour à l'autre

En analysant ces deux cas, on remarque qu'ils ont tous les deux la même structure :
- une requête SQL qui retourne une valeur
- une comparaison de cette valeur à un seuil
- une alerte si ça dépasse

La première idée était donc de coder ces règles en Python, avec un dispatcher
qui lit un "ruleType" dans la config et appelle la bonne fonction.

Mais Christophe a précisé quelque chose de plus important dans le ticket :
il existe déjà une table centrale qui centralise tous ces résultats de contrôle,
créée par d'autres équipes : interne_data.monitoring_events.

Cette table reçoit déjà les résultats de règles qui tournent dans le datalake.
Chaque ligne représente un événement avec un statut : OK, ALERTE ou CRITIQUE.

Du coup, notre rôle n'est pas de recalculer les règles — c'est déjà fait ailleurs.
Notre rôle est de lire cette table et d'envoyer les bonnes alertes aux bonnes personnes.

C'est le pattern "pub/sub" (publication / abonnement) :
  - les process métier publient des événements dans la table
  - notre script lit la table et notifie les abonnés selon leurs filtres


LA STRUCTURE DE LA TABLE monitoring_events
-------------------------------------------

Voici ce que contient chaque ligne de la table :

  source                : d'où vient l'événement (ex: ouigos3dfr_crm)
  source_detail         : détail (ex: actionable_export_booking)
  source_type           : type de source (iceberg, batch, ...)
  rule_category         : catégorie de la règle (data_quality, anomaly_detection, ...)
  rule                  : nom de la règle (ex: nbr_hard_error_variation)
  process_date          : date à laquelle la donnée a été traitée
  metric_name           : nom de la mesure (ex: delta_error)
  metric_value          : valeur observée (ex: 0.0)
  threshold_value       : valeur de seuil (ex: 5.0)
  status                : OK / ALERTE / CRITIQUE
  message               : explication si pas OK
  event_creation_date   : quand l'événement a été créé
  event_modification_date : quand il a été mis à jour

On a accès aux vraies données via Zeppelin. Sur les données qu'on a vues,
tout est à "OK" — les règles existantes n'ont pas détecté d'anomalie.


CE QUE FAIT LE SCRIPT GenericMonitoring
-----------------------------------------

Le script tourne périodiquement (via Airflow en prod).
A chaque exécution, il :

1. Lit le fichier config.json
2. Pour chaque abonnement actif :
   a. Ouvre une connexion Impala (DSN ODBC Windows)
   b. Construit un SQL dynamiquement selon les filtres de l'abonnement
   c. Exécute le SQL sur interne_data.monitoring_events
   d. Si des lignes remontent → envoie un mail HTML avec un tableau
   e. Si aucune ligne → rien, on logue juste "no events"
3. Si une erreur technique arrive (connexion échoue, etc.) → mail d'erreur à l'équipe tech

Le SQL est construit par la fonction build_query() dans main.py.
Elle assemble les conditions WHERE à partir des filtres configurés :
  - deltaHours → process_date >= now() - interval X hours
  - criticality → status IN ('ALERTE', 'CRITIQUE') ou status = 'CRITIQUE'
  - source → source = 'ouigos3dfr_global'

Exemple de SQL généré pour l'abonnement Cyllene :
  SELECT source, source_detail, process_date, rule, status, message
  FROM interne_data.monitoring_events
  WHERE process_date >= now() - interval 24 hours
  AND status IN ('ALERTE', 'CRITIQUE')
  ORDER BY status DESC, source, process_date DESC


POURQUOI UN FICHIER DE CONFIG
-------------------------------

Le fichier config.json contient tout ce qui peut changer sans modifier le code :
  - les connexions BDD et SMTP
  - la liste des abonnements avec leurs filtres et destinataires

Ajouter un nouvel abonnement (ex: une nouvelle équipe cliente) = copier-coller
un bloc JSON dans config.json. Le code Python ne change pas.

Si demain Ouigo veut recevoir uniquement les CRITIQUE en temps réel (deltaHours: 1),
on ajoute un abonnement, on ne touche pas au code.


LES ABONNEMENTS CONFIGURÉS
----------------------------

Abonnement 1 — alerte_global_cyllene
  Filtre : toutes sources, statut ALERTE ou CRITIQUE, dernières 24h
  Destinataire : cyllene-data-exploitation@groupe-cyllene.com
  Usage : vision globale du datalake pour l'équipe exploitation Cyllene

Abonnement 2 — alerte_ouigos3dfr_global
  Filtre : source = ouigos3dfr_global, statut ALERTE ou CRITIQUE, dernières 24h
  Destinataire : OuigoS3DataFR-exploitation@groupe-cyllene.com
  Usage : alertes spécifiques Ouigo pour leur propre équipe d'exploitation

Les deux peuvent coexister et envoyer des mails indépendamment.
Si un événement Ouigo est en ALERTE, les deux abonnements le reçoivent
(l'un parce qu'il voit tout, l'autre parce qu'il filtre sur Ouigo).


MULTI-CONNEXIONS
-----------------

Christophe a mentionné qu'il pourrait y avoir d'autres clients avec d'autres BDD.
Chaque abonnement a son propre champ "connexionName" qui pointe sur une entrée
dans la section "connection" du config.

Si demain il y a un client B sur un autre cluster Impala :
  - on ajoute une connexion dans "connection" avec un nouveau DSN
  - on ajoute un abonnement avec "connexionName": "impala_client_b"
  - le script ouvre la connexion à la demande et la réutilise pour les abonnements
    qui pointent sur le même DSN (pool de connexions, pas une ouverture par abonnement)


SURVEILLANCE DE LA TABLE monitoring_events ELLE-MEME
------------------------------------------------------

Le ticket demandait aussi de surveiller que la table monitoring_events soit bien
alimentée régulièrement. Si plus personne n'écrit dans cette table, c'est signe
que quelque chose a planté en amont.

Pour ça, on s'est appuyé sur le script KMN-61 existant (iceberg-monitoring).
On a simplement ajouté une tâche dans son config.json :

  {
    "name": "monitor_monitoring_eve_freshness",
    "flux": {
      "sourceTable": "interne_data.monitoring_events",
      "dateColumn": "process_date",
      "threshold_minutes": 1
    }
  }

Même logique que les autres tables : MAX(process_date) vs maintenant.
Si la table n'est plus alimentée depuis trop longtemps → mail d'alerte.
On réutilise l'infrastructure existante sans dupliquer de code.

Note : pour l'instant ce check échoue avec une erreur de droits (User 'bclovis'
does not have privileges). Les droits SELECT sur interne_data.monitoring_events
doivent être accordés au compte de service utilisé en prod.


STRUCTURE DES FICHIERS
-----------------------

GenericMonitoring/
  src/
    main.py               → orchestrateur principal
    config/
      config.json         → abonnements, connexions, destinataires
    mail/
      smtp_mailer.py      → envoi de mails HTML ou texte via SMTP
    utils/
      monitor_utils.py    → connexion Impala, logging, mail d'erreur

Monitoring table Iceberg Project/
  iceberg-monitoring/src/
    config/config.json    → ajout de la tâche monitoring_events freshness


CE QUI RESTE A FAIRE
---------------------

Technique :
  - Obtenir les droits SELECT sur interne_data.monitoring_events (bclovis ou compte service)
  - Valider avec Christophe qu'un vrai ALERTE déclenche bien le bon mail
  - Remplacer les adresses de test par les vraies adresses de prod dans config.json
  - Créer le repo GitLab pour GenericMonitoring
  - Créer le .gitlab-ci.yml et configurer le cron Airflow

Non-technique :
  - Compléter la doc Wiki : https://wiki.groupe-cyllene.com/books/kamino-fonctionnelle/page/monitoring-devenements
