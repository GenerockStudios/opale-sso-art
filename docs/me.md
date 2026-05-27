Viewed models.py:1-27
Viewed models.py:1-15
Viewed models.py:1-34
Ran command: `mkdir -p accounts/management/commands`
Created seed_data.py
Ran command: `.\.venv\Scripts\python.exe manage.py seed_data 2>&1`
Edited seed_data.py
Ran command: `.\.venv\Scripts\python.exe manage.py seed_data 2>&1`

C'est fait ! J'ai créé un script de peuplement (Management Command) et je l'ai exécuté pour remplir ta base de données PostgreSQL avec un jeu de données complet et cohérent.

### 🚀 Données de Test Créées

Voici les identifiants que tu peux utiliser pour te connecter dès maintenant :

| Rôle             | Identifiant | Mot de passe       | Direction           |
| :--------------- | :---------- | :----------------- | :------------------ |
| **Super-Admin**  | `admin`     | `adminpassword123` | Direction Générale  |
| **Manager Tech** | `j.dupont`  | `password123`      | Direction Technique |
| **Employé Tech** | `m.tech`    | `password123`      | Direction Technique |
| **Manager DAF**  | `a.finance` | `password123`      | Dir. Financière     |
| **Employé DAF**  | `b.budget`  | `password123`      | Dir. Financière     |
| **Manager RH**   | `s.rh`      | `password123`      | Ressources Humaines |

### 🛠️ Ce qui a été configuré :

1.  **4 Directions** : Technique (DT), Financière (DAF), RH, et Direction Générale (DG).
2.  **5 Applications Métiers** :
    - `GMAO Expert` (Accès: DT, DG)
    - `Sage ERP` (Accès: DAF, DG)
    - `Zimbra Mail` (Accès: Tous)
    - `Audit Tool` (Accès: DT, DG)
    - `Hiring Flow` (Accès: RH, DG)
3.  **Habilitations** : Les accès ont été automatiquement liés selon la matrice de droits définie ci-dessus.

### 📂 Commande utilisée :

Si tu as besoin de repeupler la base plus tard (après un flush par exemple), tu peux simplement lancer :

```powershell
.\.venv\Scripts\python.exe manage.py seed_data
```

Tu peux maintenant tester la **Landing Page** et te connecter avec n'importe lequel de ces comptes pour voir le filtrage des applications en temps réel !
