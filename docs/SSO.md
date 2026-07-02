### 1. Quel est le SSO choisi ?

Le SSO d'OPALE s'appuie sur une architecture **Token-based Authentication (Web SSO par jetons signés cryptographiquement)**.
Dans cette architecture :

- **OPALE agit en tant qu'Identity Provider (IdP)** (Fournisseur d'Identité) : C'est le portail centralisé connecté à l'annuaire (Active Directory/LDAP) qui authentifie l'utilisateur.
- **Les applications satellites agissent en tant que Service Providers (SP)** (Fournisseurs de Services) : Elles délèguent l'authentification à OPALE et lui demandent de confirmer l'identité des utilisateurs.

---

### 2. Pourquoi avoir choisi cette solution ?

Ce choix technique repose sur des critères d'efficacité, de sécurité et de simplicité pour un réseau d'applications d'entreprise :

- **Légèreté absolue** : Évite d'installer et de maintenir une usine à gaz externe comme Keycloak ou Active Directory Federation Services (AD FS).
- **Sécurité cryptographique forte** : Le SSO utilise la signature native de Django (`TimestampSigner`) basée sur la clé secrète de l'application (`SECRET_KEY`). Il est mathématiquement impossible pour une application tierce ou un attaquant de falsifier ou de générer un faux jeton.
- **Jetons éphémères (Sécurité contre le vol)** : Les jetons générés ont une durée de vie maximale de **60 secondes**. S'ils sont interceptés, ils deviennent rapidement inutilisables.
- **Simplicité d'intégration pour les clients** : N'importe quelle application (qu'elle soit en Django, Node.js, PHP, ou React) peut s'intégrer au SSO en effectuant une simple redirection et un appel d'API en arrière-plan.

---

### 3. Comment l'a-t-on implémenté dans OPALE ?

L'implémentation est centralisée dans les contrôleurs de l'application `accounts` ([accounts/views.py](file:///C:/D/Work/Projets/Clients/jessica_project/accounts/views.py)) à travers deux routes clés :

#### A. La demande d'autorisation : [sso_authorize_view](file:///C:/D/Work/Projets/Clients/jessica_project/accounts/views.py#L244)

Lorsqu'un utilisateur clique sur une application du catalogue, il est redirigé vers OPALE :

1.  **Vérification de session** : Si l'utilisateur n'est pas connecté à OPALE, il est invité à s'authentifier d'abord via la page de connexion connectée à l'Active Directory.
2.  **Création du jeton** : OPALE encapsule le nom d'utilisateur et le nom de l'application cible dans un payload chiffré et signé :
    ```python
    signer = signing.TimestampSigner()
    token = signer.sign_object({'username': request.user.username, 'app': app_id})
    ```
3.  **Redirection** : OPALE renvoie l'utilisateur vers l'application cible en lui passant le jeton dans l'URL (ex: `https://mon-application.art.cm/sso/callback?token=eyJ1c2...`).

#### B. L'API de vérification : [sso_verify_view](file:///C:/D/Work/Projets/Clients/jessica_project/accounts/views.py#L289)

Dès que l'application cible reçoit le jeton de la part de l'utilisateur, elle effectue une requête de serveur à serveur vers OPALE pour des raisons de sécurité :

1.  **Vérification de la validité** : OPALE reçoit le jeton et s'assure qu'il n'a pas été modifié et qu'il a été émis il y a moins de 60 secondes :
    ```python
    payload = signer.unsign_object(token, max_age=60)
    ```
2.  **Envoi des informations** : Si le jeton est valide, OPALE renvoie les détails complets du profil de l'utilisateur en JSON :
    ```json
    {
      "valid": true,
      "username": "g.ndono",
      "first_name": "Guillaume",
      "last_name": "Ndono",
      "email": "g.ndono@art.cm",
      "role": "EMPLOYE",
      "direction": "Direction Technique"
    }
    ```
    L'application cible utilise ensuite ces données pour ouvrir la session locale de l'utilisateur sans qu'il n'ait eu besoin de saisir son mot de passe une seconde fois.
