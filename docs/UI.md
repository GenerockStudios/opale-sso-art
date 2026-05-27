C'est une excellente approche. Pour un projet en **Django**, nous allons raisonner en termes de **Templates** (HTML/UI), de **Views** (Logique) et de **Context** (Données). Comme tu as déjà le script SQL, la transition vers les modèles Django sera naturelle.

Voici la première partie détaillée, focalisée sur le **Cœur du Portail (Authentification et Espace Employé)**.

---

## Phase 1 : Authentification et Sécurité (Le Portier)

C'est l'interface qui assure le "Single Sign-On" (SSO) simplifié pour l'ART.

### 1.1. Interface : Page de Connexion (Login)

- **Objectif :** Identifier l'agent et charger sa session avec sa Direction de rattachement.
- **Éléments de l'interface :**
  - Champ Identifiant (Email professionnel).
  - Champ Mot de passe (avec option "voir le mot de passe").
  - Lien "Mot de passe oublié".
  - Branding ART (Logo, couleurs institutionnelles).
- **Logique Django :** Utilisation de `LoginView` (ou une vue personnalisée). En cas de succès, redirection vers le tableau de bord.
- **Sous-interface :**
  - **Réinitialisation de mot de passe :** Formulaire de saisie d'email envoyant un lien sécurisé par token (Django `auth_views`).

---

## Phase 2 : Le Portail "Hub" de l'Employé (Espace de Travail)

C'est l'interface principale après connexion. C'est ici que l'unification prend tout son sens.

### 2.1. Interface : Tableau de Bord Dynamique (Home)

- **Objectif :** Présenter uniquement les outils auxquels l'employé a droit.
- **Éléments de l'interface :**
  - **Barre latérale (Sidebar) :** Liens rapides (Accueil, Annuaire, Mon Profil).
  - **En-tête (Header) :** Nom de l'employé, sa Direction (ex: _Direction Technique_) et bouton déconnexion.
  - **Grille d'applications (Service Grid) :** Des cartes (Cards) cliquables. Chaque carte contient le logo du logiciel, son nom et une brève description.
- **Logique Django :**
  - La vue récupère l'ID de la direction de l'utilisateur connecté : `request.user.direction`.
  - Elle filtre les applications : `Application.objects.filter(direction_applications__direction=user.direction)`.
  - Le template utilise une boucle `{% for app in apps %}` pour générer les cartes.

### 2.2. Interface : L'Annuaire Numérique ART

- **Objectif :** Faciliter la communication entre les services.
- **Éléments de l'interface :**
  - Barre de recherche (par nom ou par poste).
  - Filtre par Direction (Menu déroulant).
  - Liste/Grille des collaborateurs avec : Photo, Nom, Direction, Email, Poste.
- **Logique Django :** Vue de type `ListView` sur le modèle `Utilisateur`. Implémentation de filtres `Q` pour la recherche multi-critères.
- **Sous-interface :**
  - **Fiche de contact :** Une fenêtre modale (Pop-up) affichant les détails complets d'un collègue quand on clique sur son nom.

### 2.3. Interface : Gestion du Profil (Settings)

- **Objectif :** Autonomie de l'agent sur ses informations.
- **Éléments de l'interface :**
  - Section "Informations Personnelles" (Nom, Email - souvent en lecture seule).
  - Section "Photo de Profil" (Upload d'image).
  - Section "Sécurité" (Changement de mot de passe).
- **Logique Django :** Utilisation de `UpdateView` et de `UserPassesTestMixin` pour garantir que l'utilisateur ne modifie que son propre profil.

---

## Phase 3 : L'Espace d'Administration (Gouvernance)

C'est ici que l'administrateur système de l'ART pilote la plateforme.

### 3.1. Interface : Console de Gestion des Directions

- **Objectif :** Refléter l'organigramme de l'agence.
- **Éléments de l'interface :**
  - Tableau récapitulatif des directions (Code, Nom, Nombre d'employés).
  - Bouton "Ajouter une Direction".
- **Sous-interface :**
  - **Éditeur de Direction :** Formulaire de saisie du nom, code et description.

### 3.2. Interface : Catalogue des Applications et Habilitations

- **Objectif :** Gérer le parc logiciel et qui y accède. C'est l'interface la plus critique.
- **Éléments de l'interface :**
  - Liste des logiciels enregistrés avec bouton de statut (Actif/Inactif).
  - **Matrice de Droits :** Une vue spécifique où l'admin peut cocher quelles directions ont accès à quel logiciel.
- **Logique Django :** Formulaire de type `ModelForm` avec un widget `CheckboxSelectMultiple` pour gérer la relation Many-to-Many entre Directions et Applications.

### 3.3. Interface : Monitoring et Logs d'Audit

- **Objectif :** Assurer la traçabilité des accès.
- **Éléments de l'interface :**
  - Journal des événements sous forme de table (Date, Utilisateur, Action, Logiciel accédé).
  - Filtres par date et par utilisateur.
- **Logique Django :** Lecture seule du modèle `LogsActivite`. Pagination obligatoire (car les logs peuvent devenir volumineux).

---

### Résumé pour ta TODO List Django :

1.  [ ] **App `core` :** Modèles personnalisés (AbstractUser), Directions, Applications.
2.  [ ] **App `auth` :** Vues de login, logout et gestion de profil.
3.  [ ] **App `portal` :** Vue du tableau de bord (filtrage par direction).
4.  [ ] **App `directory` :** Vue de recherche et liste des employés.
5.  [ ] **App `admin_custom` :** Vues de gestion des directions et des habilitations (différent de l'admin Django par défaut pour être plus "User Friendly").

Est-ce que cette répartition te semble assez granulaire pour attaquer ton développement, ou souhaites-tu que j'approfondisse un module spécifique (comme la logique technique du SSO ou le système de logs) ?
