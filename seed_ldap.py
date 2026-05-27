import sys
from ldap3 import Server, Connection, ALL, MODIFY_ADD

def seed_ldap():
    print("Sowing the seeds of the Active Directory / OpenLDAP server...")
    server = Server('ldap://localhost:389', get_info=ALL)
    
    # Bind to LDAP server as admin
    try:
        conn = Connection(server, user='cn=admin,dc=art,dc=cm', password='adminpassword', auto_bind=True)
    except Exception as e:
        print(f"[-] Erreur de connexion à l'annuaire LDAP : {e}")
        sys.exit(1)
        
    print("[+] Connecté à l'annuaire LDAP en tant que admin.")
    
    # 1. Créer l'unité organisationnelle pour les utilisateurs et groupes si non existants
    ous = [
        ('ou=users,dc=art,dc=cm', 'users'),
        ('ou=groups,dc=art,dc=cm', 'groups'),
    ]
    
    for dn, name in ous:
        try:
            conn.add(dn, object_class=['organizationalUnit', 'top'], attributes={'ou': name})
            print(f"  [+] OU créée : {dn}")
        except Exception as e:
            if 'entryAlreadyExists' in str(e):
                print(f"  [.] OU existe déjà : {dn}")
            else:
                print(f"  [-] Erreur OU {dn} : {e}")

    # 2. Créer les groupes (ex: managers, admins, techniciens)
    groups = [
        ('cn=managers,ou=groups,dc=art,dc=cm', 'managers'),
        ('cn=admins,ou=groups,dc=art,dc=cm', 'admins'),
    ]
    for dn, name in groups:
        try:
            # We initialize with the admin DN to satisfy the schema requirement of having at least one member
            conn.add(dn, object_class=['groupOfNames', 'top'], attributes={'cn': name, 'member': 'cn=admin,dc=art,dc=cm'})
            print(f"  [+] Groupe créé : {dn}")
        except Exception as e:
            if 'entryAlreadyExists' in str(e):
                print(f"  [.] Groupe existe déjà : {dn}")
            else:
                print(f"  [-] Erreur groupe {dn} : {e}")

    # 3. Créer les utilisateurs simulés de l'AD
    users_data = [
        {
            'uid': 'j.dupont',
            'cn': 'Jean Dupont',
            'sn': 'Dupont',
            'givenName': 'Jean',
            'mail': 'j.dupont@art.cm',
            'ou': 'Direction Technique',
            'password': 'password123',
            'role': 'MANAGER'
        },
        {
            'uid': 'm.tech',
            'cn': 'Michel Technique',
            'sn': 'Technique',
            'givenName': 'Michel',
            'mail': 'm.tech@art.cm',
            'ou': 'Direction Technique',
            'password': 'password123',
            'role': 'EMPLOYE'
        },
        {
            'uid': 'a.finance',
            'cn': 'Alice Comptable',
            'sn': 'Comptable',
            'givenName': 'Alice',
            'mail': 'a.finance@art.cm',
            'ou': 'Direction Financière',
            'password': 'password123',
            'role': 'MANAGER'
        },
        {
            'uid': 's.rh',
            'cn': 'Sarah Recrutement',
            'sn': 'Recrutement',
            'givenName': 'Sarah',
            'mail': 's.rh@art.cm',
            'ou': 'Ressources Humaines',
            'password': 'password123',
            'role': 'MANAGER'
        },
        {
            'uid': 'g.ndono',
            'cn': 'Guillaume Ndono',
            'sn': 'Ndono',
            'givenName': 'Guillaume',
            'mail': 'g.ndono@art.cm',
            'ou': 'Direction Technique',
            'password': 'password123',
            'role': 'EMPLOYE'
        }
    ]

    for u in users_data:
        dn = f"uid={u['uid']},ou=users,dc=art,dc=cm"
        attrs = {
            'cn': u['cn'],
            'sn': u['sn'],
            'givenName': u['givenName'],
            'mail': u['mail'],
            'ou': u['ou'],
            'title': u['role'], # store role in standard title attribute
            'userPassword': u['password'],
        }
        
        # Check if user already exists. If yes, we delete and recreate to ensure clean attributes
        try:
            conn.search('dc=art,dc=cm', f'(uid={u["uid"]})')
            if conn.entries:
                conn.delete(dn)
                print(f"  [-] Supprimé utilisateur existant pour mise à jour : {dn}")
        except Exception:
            pass

        try:
            conn.add(dn, object_class=['inetOrgPerson', 'organizationalPerson', 'person', 'top'], attributes=attrs)
            print(f"  [+] Utilisateur créé : {dn} avec rôle {u['role']}")
            
            # Ajouter aux groupes selon rôle
            if u['role'] == 'MANAGER':
                try:
                    conn.modify('cn=managers,ou=groups,dc=art,dc=cm', {'member': [(MODIFY_ADD, [dn])]})
                    print(f"    [+] Ajouté au groupe managers : {u['uid']}")
                except Exception as ex:
                    print(f"    [-] Erreur ajout groupe managers : {ex}")
            elif u['role'] == 'ADMIN':
                try:
                    conn.modify('cn=admins,ou=groups,dc=art,dc=cm', {'member': [(MODIFY_ADD, [dn])]})
                    print(f"    [+] Ajouté au groupe admins : {u['uid']}")
                except Exception as ex:
                    print(f"    [-] Erreur ajout groupe admins : {ex}")
        except Exception as e:
            print(f"  [-] Erreur utilisateur {dn} : {e}")

    # Let's perform a simple search to verify everything
    print("[+] Recherche de vérification...")
    conn.search('dc=art,dc=cm', '(objectClass=inetOrgPerson)', attributes=['cn', 'mail', 'ou', 'title'])
    for entry in conn.entries:
        print(f"  [V] Trouvé : {entry.cn} ({entry.mail}) dans {entry.ou} (Rôle: {entry.title})")

    print("\n[SUCCESS] L'annuaire LDAP d'ART Cameroun a été peuplé avec succès.")

if __name__ == "__main__":
    seed_ldap()
