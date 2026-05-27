# Documentation Technique UML — Projet OPALE

---

## 1. Diagramme de Cas d'Utilisation (Use Case Diagram)

### Description

Ce diagramme identifie les deux acteurs principaux du système OPALE et leurs interactions. L'**Utilisateur** (Collaborateur ou Manager) est le principal consommateur du Hub. L'**Administrateur** hérite de tous les cas d'utilisation de l'Utilisateur et dispose de fonctions de gestion étendues. Le cas « Lancer une Application » inclut systématiquement la vérification des droits directionnels, cœur du mécanisme d'habilitation d'OPALE.

```mermaid
graph LR
    Utilisateur["👤 Utilisateur\n(Collaborateur / Manager)"]
    Admin["🔑 Administrateur"]

    subgraph OPALE ["Système OPALE — Service Hub ART"]
        UC1(["S'authentifier"])
        UC2(["Consulter le Dashboard"])
        UC3(["Lancer une Application"])
        UC4(["Vérifier les\nDroits d'accès"])
        UC5(["Gérer son Profil"])
        UC6(["Consulter l'Annuaire"])
        UC7(["Gérer les Utilisateurs"])
        UC8(["Gérer le Catalogue\ndes Applications"])
        UC9(["Gérer la Matrice\ndes Droits"])
        UC10(["Consulter les\nLogs d'Audit"])
        UC11(["Journaliser\nl'Activité"])
        UC12(["Désactiver / Activer\nun Compte"])
        UC13(["Filtrer les Logs"])

        %% «include» — sous-comportement OBLIGATOIRE
        UC3 -.->|"«include»"| UC4
        UC3 -.->|"«include»"| UC11
        UC7 -.->|"«include»"| UC11
        UC9 -.->|"«include»"| UC11

        %% «extend» — comportement OPTIONNEL conditionnel
        UC12 -.->|"«extend»"| UC7
        UC13 -.->|"«extend»"| UC10
    end

    %% Généralisation entre acteurs (Admin hérite de Utilisateur)
    Admin -->|"«héritage»"| Utilisateur

    Utilisateur --> UC1
    Utilisateur --> UC2
    Utilisateur --> UC3
    Utilisateur --> UC5
    Utilisateur --> UC6

    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10

    style Utilisateur fill:#e8f4f8,color:#333,stroke:#4a90d9
    style Admin fill:#f8e8e8,color:#333,stroke:#d94a4a
    style OPALE fill:#fbfdff,color:#333,stroke:#4a90d9
```

---

## 2. Diagramme de Classes (Class Diagram)

### Description

Ce diagramme représente le schéma de données complet du projet, en correspondance exacte avec les modèles définis dans le code métier (`models.py`). La classe **`Utilisateur`** regroupe les informations du profil. La **`Direction`** est le pivot de sécurité central. **`DirectionApplication`** est la classe d'association de la relation entre une direction et plusieurs applications (l'habilitation). **`LogActivite`** trace chaque action réalisée. Les associations sont bidirectionnelles (sans flèche) et annotées de verbes à l'infinitif.

```mermaid
classDiagram
    direction TB

    class Utilisateur {
        - id : int
        - username : String
        - password : String
        - email : String
        - first_name : String
        - last_name : String
        - is_active : boolean
        - date_joined : Date
        - role : String
        + get_full_name() String
    }

    class Direction {
        - id : int
        - nom : String
        - code : String
        - description : String
        - created_at : Date
    }

    class Application {
        - id : int
        - nom : String
        - url_acces : String
        - icone_name : String
        - description : String
        - est_actif : boolean
        - created_at : Date
    }

    class DirectionApplication {
        <<classe-association>>
        - date_attribution : Date
    }

    class LogActivite {
        - id : int
        - action : String
        - ip_address : String
        - details : String
        - cree_le : Date
    }

    Direction "0..1" -- "0..*" Utilisateur : employer
    Utilisateur "0..1" -- "0..*" LogActivite : générer
    Direction "0..*" -- "0..*" Application : habiliter
    DirectionApplication .. Direction
    DirectionApplication .. Application
```

---

## 3. Diagrammes de Séquence

---

### SD 1 : Authentification Sécurisée

**Description :** Ce diagramme modélise le processus de connexion d'un utilisateur au portail OPALE. L'utilisateur soumet ses identifiants. Le système vérifie les informations en base de données. Si la vérification réussit, une session est créée, la connexion est journalisée, et l'utilisateur est redirigé vers son tableau de bord personnalisé. En cas d'échec, la tentative est également tracée et un message d'erreur est affiché.

```mermaid
sequenceDiagram
    autonumber
    actor Utilisateur
    participant Systeme as : Système
    participant JournalAudit as : JournalAudit
    participant Base as : Base de données

    Utilisateur->>+Systeme: saisir les identifiants
    Systeme->>+Base: rechercher le compte utilisateur
    Base-->>-Systeme: données du compte

    alt identifiants incorrects
        Systeme->>JournalAudit: créer une trace d'échec
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>Utilisateur: afficher un message d'erreur
    else identifiants corrects
        Systeme->>Systeme: vérifier le mot de passe
        Systeme->>Base: ouvrir une session utilisateur
        Base-->>Systeme: session enregistrée
        Systeme->>JournalAudit: créer une trace de connexion
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>-Utilisateur: afficher le tableau de bord
    end
```

---

### SD 2 : Lancement d'une Application Métier

**Description :** Ce flux est le cœur du Hub OPALE. Lorsqu'un utilisateur clique sur une application, le système vérifie en temps réel que sa direction est bien habilitée pour cet accès. Si l'habilitation est confirmée, l'événement est tracé dans le journal d'audit et l'utilisateur est redirigé vers l'application. Tout accès non autorisé est également journalisé et l'utilisateur en est refusé l'accès.

```mermaid
sequenceDiagram
    autonumber
    actor Utilisateur
    participant Systeme as : Système
    participant JournalAudit as : JournalAudit
    participant Base as : Base de données

    rect rgb(240, 248, 255)
        Note over Utilisateur, Base: réf. SD1 — l'utilisateur dispose d'une session active
    end

    Utilisateur->>+Systeme: sélectionner une application
    Systeme->>+Base: vérifier les droits d'accès
    Base-->>-Systeme: résultat de la vérification

    alt direction non habilitée
        Systeme->>JournalAudit: créer une trace de refus
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>Utilisateur: afficher un message de refus
    else direction habilitée
        Systeme->>JournalAudit: créer une trace d'accès accordé
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>-Utilisateur: ouvrir l'application
    end
```

---

### SD 3 : Gestion CRUD des Utilisateurs (par l'Administrateur)

**Description :** Ce diagramme décrit le cycle complet de création d'un compte utilisateur. L'administrateur remplit les informations. Le système valide les données saisies, sécurise le mot de passe avant stockage, puis enregistre le nouveau compte en base de données. L'action est tracée dans le journal d'audit.

```mermaid
sequenceDiagram
    autonumber
    actor Administrateur
    participant Systeme as : Système
    participant JournalAudit as : JournalAudit
    participant Base as : Base de données

    rect rgb(240, 248, 255)
        Note over Administrateur, Base: réf. SD1 — l'administrateur dispose d'une session active
    end

    Administrateur->>+Systeme: saisir les informations du compte
    Systeme->>Systeme: valider les données saisies

    alt données invalides
        Systeme-->>Administrateur: afficher les erreurs
    else données valides
        Systeme->>Systeme: chiffrer le mot de passe
        Systeme->>+Base: enregistrer le compte
        Base-->>-Systeme: compte créé
        Systeme->>JournalAudit: créer une trace de création
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>-Administrateur: confirmer la création
    end
```

---

### SD 4 : Attribution des Droits — Matrice Directions/Applications

**Description :** L'administrateur modifie les droits d'accès sous forme de grille. L'habilitation est créée ou supprimée selon si elle existait.

```mermaid
sequenceDiagram
    autonumber
    actor Administrateur
    participant Systeme as : Système
    participant JournalAudit as : JournalAudit
    participant Base as : Base de données

    rect rgb(240, 248, 255)
        Note over Administrateur, Base: réf. SD1 — l'administrateur dispose d'une session active
    end

    Administrateur->>+Systeme: modifier l'accès d'une direction
    Systeme->>+Base: vérifier si l'habilitation existe déjà
    Base-->>-Systeme: résultat de la vérification

    alt habilitation inexistante — attribution
        Systeme->>Base: créer l'habilitation
        Base-->>Systeme: confirmé
        Systeme->>JournalAudit: créer une trace d'attribution
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>Administrateur: accès accordé
    else habilitation existante — révocation
        Systeme->>Base: supprimer l'habilitation
        Base-->>Systeme: confirmé
        Systeme->>JournalAudit: créer une trace de révocation
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>-Administrateur: accès retiré
    end
```

---

### SD 5 : Mise à jour du Profil Collaborateur

**Description :** Ce diagramme décrit la mise à jour des informations personnelles d'un collaborateur.

```mermaid
sequenceDiagram
    autonumber
    actor Utilisateur
    participant Systeme as : Système
    participant JournalAudit as : JournalAudit
    participant Base as : Base de données

    rect rgb(240, 248, 255)
        Note over Utilisateur, Base: réf. SD1 — l'utilisateur dispose d'une session active
    end

    Utilisateur->>+Systeme: modifier ses informations personnelles
    Systeme->>Systeme: valider les données

    alt données invalides
        Systeme-->>Utilisateur: afficher les erreurs
    else données valides
        Systeme->>+Base: mettre à jour le compte
        Base-->>-Systeme: modification enregistrée
        Systeme->>JournalAudit: créer une trace de mise à jour
        JournalAudit->>Base: enregistrer le journal
        Systeme-->>-Utilisateur: confirmer la mise à jour
    end
```

---

## 4. Diagramme d'Activité (Activity Diagram)

### Description

Ce diagramme modélise le processus global d'un employé depuis l'accès au portail jusqu'au lancement d'une application. Trois points de contrôle critiques structurent ce flux :

1. **Vérification de Session :** Présence d'une session valide ou redirection vers la page de login.
2. **Filtrage par Direction :** Le tableau de bord n'affiche que les applications pour lesquelles la direction de l'utilisateur est habilitée.
3. **Contrôle au Lancement :** Vérification redondante et systématique à chaque tentative de lancement, garantissant qu'un accès direct à l'URL est également bloqué.

```mermaid
flowchart TD
    Start(["Début — Accès OPALE"])
    CheckSession{{"Session\nvalide ?"}}
    LoginPage[/"Page de Connexion"/]
    CheckCredentials{{"Identifiants\ncorrects ?"}}
    LoginError[/"Erreur — Identifiants invalides"/]
    LoadProfile["Chargement du Profil Utilisateur"]
    FilterApps["Filtrage des Applications\npar Direction et Statut Actif"]
    CheckDirection{{"Direction\nassignée ?"}}
    EmptyDash[/"Tableau de bord vide\n(aucune application disponible)"/]
    LoadDash[/"Affichage du Tableau de Bord\n(applications autorisées)"/]
    SelectApp["Sélection d'une Application"]
    LaunchCheck{{"Direction habilitée\npour cette application ?"}}
    AccessDenied[/"Accès refusé\nJournalisation du refus\nRetour au tableau de bord"/]
    LogEvent["Journalisation de l'accès\n(utilisateur, application, IP, horodatage)"]
    Redirect["Redirection vers l'application"]
    ExternalApp(["Application Métier chargée"])
    End(["Fin de Session"])

    Start --> CheckSession
    CheckSession -->|"Non"| LoginPage
    CheckSession -->|"Oui"| LoadProfile
    LoginPage --> CheckCredentials
    CheckCredentials -->|"Non"| LoginError
    LoginError --> LoginPage
    CheckCredentials -->|"Oui"| LoadProfile

    LoadProfile --> CheckDirection
    CheckDirection -->|"Non"| EmptyDash
    CheckDirection -->|"Oui"| FilterApps
    EmptyDash --> End

    FilterApps --> LoadDash
    LoadDash --> SelectApp
    SelectApp --> LaunchCheck

    LaunchCheck -->|"Non"| AccessDenied
    AccessDenied --> LoadDash

    LaunchCheck -->|"Oui"| LogEvent
    LogEvent --> Redirect
    Redirect --> ExternalApp
    ExternalApp --> End

    style Start fill:#e8f8f5,color:#1a472a,stroke:#2ecc71
    style End fill:#fdedec,color:#922b21,stroke:#e74c3c
    style ExternalApp fill:#ebf5fb,color:#1a3a5c,stroke:#3498db
    style AccessDenied fill:#f9ebea,color:#7d2c2c,stroke:#e74c3c
    style LogEvent fill:#f4ecf7,color:#4a235a,stroke:#9b59b6
    style LaunchCheck fill:#ebedef,color:#2c3e50,stroke:#bdc3c7
    style CheckSession fill:#ebedef,color:#2c3e50,stroke:#bdc3c7
    style CheckCredentials fill:#ebedef,color:#2c3e50,stroke:#bdc3c7
    style CheckDirection fill:#ebedef,color:#2c3e50,stroke:#bdc3c7
```

---

## 5. Architecture des Modules — Vue des Dépendances

```mermaid
graph LR
    subgraph opale_project["opale_project — Configuration centrale"]
        settings["settings.py\nModèle utilisateur personnalisé"]
    end

    subgraph accounts["accounts — Gestion des Utilisateurs"]
        A_M["Utilisateur\n(modèle)"]
        A_V["Vues\nprofil · annuaire · CRUD admin"]
        A_F["Formulaires\nProfil · Création admin"]
    end

    subgraph organizations["organizations — Structure Organisationnelle"]
        O_M["Direction\n(modèle)"]
    end

    subgraph catalogue["catalogue — Catalogue des Applications"]
        C_M["Application · Habilitation\n(modèles)"]
        C_V["Vues\nTableau de bord · Lancement · CRUD"]
        C_F["Formulaires\nApplication"]
    end

    subgraph audit["audit — Traçabilité & Sécurité"]
        AU_M["Journal\n(modèle)"]
        AU_V["Vues\nDashboard audit · Matrice · Toggle"]
        AU_L["Logique\nJournalisation · Extraction IP"]
    end

    O_M --> A_M
    O_M --> C_M
    A_M --> AU_M
    AU_L --> AU_M
    C_V --> AU_L
    A_V --> AU_L
    AU_V --> AU_L
    settings --> A_M

    style opale_project fill:#eaedf4,color:#333,stroke:#4a90d9
    style accounts fill:#e8effa,color:#333,stroke:#4a90d9
    style organizations fill:#eafaf0,color:#333,stroke:#2ecc71
    style catalogue fill:#f2eafa,color:#333,stroke:#9b59b6
    style audit fill:#faebea,color:#333,stroke:#e74c3c
```

---
