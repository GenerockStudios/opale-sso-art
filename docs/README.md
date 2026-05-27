# OPALE — Service Hub Unifié de l'ART (Cameroun)

Ce projet est un portail captif fédérateur développé pour l'**Agence de Régulation des Télécommunications (ART) du Cameroun**, démontrant l'intégration d'une authentification centralisée **Single Sign-On (SSO)** et d'un annuaire **Active Directory / OpenLDAP**.

---

## Architecture de Déploiement Local

Pour un réalisme absolu, l'architecture locale s'appuie entièrement sur **Docker** pour faire tourner les bases relationnelles et l'annuaire d'entreprise réel :

- **opale_db** : Conteneur PostgreSQL 16 écoutant sur le port **5434** (port modifié pour contourner les conflits avec un serveur Postgres Windows préexistant).
- **opale_ldap** : Conteneur d'annuaire OpenLDAP écoutant sur le port **389** (et sécurisé sur le port 636).

---

## Guide d'Installation et Initialisation

### 1. Prérequis

- **Python 3.10+** (Testé avec Python 3.13)
- **Docker Desktop** (pour les bases PostgreSQL et l'annuaire OpenLDAP)

### 2. Configuration Initiale

Si vous venez de cloner ou de copier le projet pour la première fois :

1. **Lancer les Services Docker (Base & Annuaire) :**
   Depuis la racine du projet, lancez :
   ```powershell
   docker compose up -d
   ```
   *Cela va télécharger, instancier et exécuter automatiquement PostgreSQL (port 5434) et OpenLDAP (port 389).*

2. **Créer l'Environnement Virtuel Python :**
   ```powershell
   python -m venv .venv
   ```

3. **Activer l'Environnement :**
   ```powershell
   .\.venv\Scripts\activate
   ```

4. **Installer les Dépendances (y compris ldap3) :**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Initialiser la Base de Données Relationnelle (Django) :**
   ```powershell
   python manage.py migrate
   python seeds.py
   ```
   *Le script `seeds.py` peuple les tables Django avec les directions et enregistre les 3 nouvelles applications PoC (Zimbra Mail, Concessions, Supervision du Spectre) ainsi que la matrice des droits.*

6. **Peupler l'Annuaire OpenLDAP d'Entreprise :**
   Exécutez notre script d'injection LDAP :
   ```powershell
   python seed_ldap.py
   ```
   *Ce script se connecte en admin à votre conteneur OpenLDAP Docker, crée la structure d'organisation de l'ART (utilisateurs, attributs de profil, groupes de rôles) et injecte les 5 comptes de test.*

---

## 📡 Exécution & Présentation (Soutenance)

1. **Démarrer le Serveur de Développement Django :**
   ```powershell
   .\.venv\Scripts\activate
   python manage.py runserver
   ```
   Le portail est accessible à l'adresse : **[http://localhost:8000/](http://localhost:8000/)**

2. **Scénario de Démonstration en Direct (SSO & Sécurité) :**
   - **Étape 1 : Connexion AD**
     Connectez-vous sur la page de connexion unique avec le compte AD inédit `g.ndono` (mot de passe : `password123`).
     *Le backend interroge OpenLDAP en temps réel, valide le mot de passe, extrait ses claims et crée son compte Django à la volée, le liant directement à la Direction Technique.*
   
   - **Étape 2 : SSO Standalone (Nouvel Onglet)**
     Depuis le tableau de bord d'OPALE, cliquez sur **Zimbra Mail** ou **Supervision du Spectre**.
     L'application s'ouvre dans un **nouvel onglet** en **plein écran** (fullscreen standalone, avec sa propre interface) et se connecte silencieusement par Single Sign-On en moins de 50 ms.
   
   - **Étape 3 : La SSO Debug Console**
     Cliquez sur le **bouton flottant bleu pulsant** (en bas à droite). Le panneau glassmorphic sombre glisse de la droite et écrit en temps réel (vitesse machine à écrire) toutes les étapes cryptographiques et réseau du handshake de sécurité SSO. Vous pouvez cliquer sur **"Rejouer la cinématique"** pour faire une nouvelle démonstration immédiate.
   
   - **Étape 4 : Le Blocage de Sécurité (ABAC)**
     Connectez-vous avec le compte RH `s.rh` (mot de passe : `password123`) et tentez d'accéder au "Suivi des Licences". Vous serez bloqué de manière sécurisée par un écran rouge d'Accès Refusé personnalisé qui extrait et affiche vos attributs de profil non conformes.

---

## 👥 Matrice des Utilisateurs de Test

| Identifiant | Mot de Passe | Type de Compte | Direction (LDAP) | Rôle |
| :--- | :--- | :--- | :--- | :---: |
| `g.ndono` | `password123` | **LDAP (Docker)** | Direction Technique | EMPLOYE |
| `j.dupont` | `password123` | **LDAP (Docker)** | Direction Technique | MANAGER |
| `a.finance` | `password123` | **LDAP (Docker)** | Direction Financière | MANAGER |
| `s.rh` | `password123` | **LDAP (Docker)** | Ressources Humaines | MANAGER |
| `admin_art` | `art_2026` | **Base Django Locale** | Direction Technique | ADMIN (Superuser) |
