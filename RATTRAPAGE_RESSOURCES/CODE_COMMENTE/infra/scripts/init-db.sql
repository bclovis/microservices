-- =============================================================================
-- INFRA — init-db.sql
-- Script d'initialisation des bases de données PostgreSQL
-- =============================================================================
-- RÔLE DU FICHIER :
-- Ce script est exécuté AUTOMATIQUEMENT par PostgreSQL au premier démarrage.
-- Il est monté dans /docker-entrypoint-initdb.d/ dans le container Postgres.
-- Tout fichier .sql dans ce dossier est exécuté lors de l'initialisation.
--
-- POURQUOI 4 BASES SÉPARÉES ?
-- Principe des microservices : chaque service a SA PROPRE base de données.
-- Battle Service NE PEUT PAS accéder à auth_db directement (isolation des données).
-- Si on voulait une info d'un autre service, on ferait un appel HTTP ou via Kafka.
-- =============================================================================

-- Base pour le service d'authentification (users, tokens JWT)
CREATE DATABASE auth_db;

-- Base pour le service de gestion des équipes Pokémon (teams, pokémon slots)
CREATE DATABASE team_db;

-- Base pour le moteur de combat (battles, rounds, résultats)
CREATE DATABASE battle_db;

-- Base pour le chat (messages, historique des conversations)
CREATE DATABASE chat_db;

-- =============================================================================
-- NOTE : SQLAlchemy crée automatiquement les TABLES dans chaque base
-- via Base.metadata.create_all() lors du démarrage de chaque service.
-- Ce fichier crée uniquement les BASES (containers de tables).
-- =============================================================================
