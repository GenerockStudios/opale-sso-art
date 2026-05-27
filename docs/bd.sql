-- #############################################################
-- # PROJET : PORTAIL WEB UNIFIÉ - ART
-- # SGBD : POSTGRESQL
-- # DESCRIPTION : GESTION DES ACCÈS AUX LOGICIELS PAR DIRECTION
-- #############################################################

-- Extension pour la génération de UUID si nécessaire (optionnel)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

BEGIN;

-- 1. Table des Directions (Organigramme de l'ART)
CREATE TABLE directions (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL UNIQUE,
    code VARCHAR(10) UNIQUE, -- ex: DAJ, DT, DAF
    description TEXT,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table des Logiciels (Catalogue applicatif)
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    url_acces TEXT NOT NULL,
    icone_url TEXT,
    description TEXT,
    est_actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Table des Utilisateurs
-- On lie chaque employé à une seule direction (Règle métier)
CREATE TABLE utilisateurs (
    id SERIAL PRIMARY KEY,
    nom_complet VARCHAR(200) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL, -- Hash Argon2 ou BCrypt
    role VARCHAR(50) DEFAULT 'EMPLOYE', -- EMPLOYE, ADMIN, MANAGER
    direction_id INTEGER REFERENCES directions (id) ON DELETE SET NULL,
    derniere_connexion TIMESTAMP
    WITH
        TIME ZONE,
        est_actif BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Table Pivot : Habilitations (Quelle direction accède à quel logiciel)
CREATE TABLE direction_applications (
    direction_id INTEGER REFERENCES directions (id) ON DELETE CASCADE,
    application_id INTEGER REFERENCES applications (id) ON DELETE CASCADE,
    date_attribution TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (direction_id, application_id)
);

-- 5. Table d'Audit (Pour la traçabilité demandée)
CREATE TABLE logs_activite (
    id BIGSERIAL PRIMARY KEY,
    utilisateur_id INTEGER REFERENCES utilisateurs (id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL, -- ex: "Accès Logiciel RH", "Connexion Portail"
    details JSONB, -- Pour stocker des métadonnées (IP, Navigateur)
    cree_le TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);