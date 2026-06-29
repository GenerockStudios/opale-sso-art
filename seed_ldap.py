import sys
import os
import json
from ldap3 import Server, Connection, ALL, MODIFY_ADD, MODIFY_REPLACE

def seed_ldap():
    print("Sowing the seeds of the Active Directory / OpenLDAP server...")
    
    # Configuration par défaut
    config = {
        'SERVER_TYPE': 'OPENLDAP',
        'SERVER': 'ldap://localhost:389',
        'DOMAIN': 'art.cm',
        'BASE_DN': 'dc=art,dc=cm',
        'USER_OU': 'ou=users,dc=art,dc=cm',
        'GROUP_OU': 'ou=groups,dc=art,dc=cm',
        'BIND_USER': 'cn=admin,dc=art,dc=cm',
        'BIND_PASSWORD': 'adminpassword',
        'USE_SSL': False
    }
    
    # Charger le fichier JSON si présent
    config_path = os.path.join(os.path.dirname(__file__), 'ldap_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
                for k, v in json_config.items():
                    if k == 'SERVER_URL':
                        config['SERVER'] = v
                    else:
                        config[k] = v
            print(f"[+] Configuration chargée depuis {config_path}")
        except Exception as e:
            print(f"[-] Erreur de chargement de la config : {e}")

    server_type = config.get('SERVER_TYPE', 'ACTIVE_DIRECTORY').upper()
    server_url = config.get('SERVER', 'ldap://localhost:389')
    use_ssl = config.get('USE_SSL', False) or server_url.startswith('ldaps://')
    
    server = Server(server_url, use_ssl=use_ssl, get_info=ALL)
    
    # Bind to LDAP server
    try:
        conn = Connection(server, user=config['BIND_USER'], password=config['BIND_PASSWORD'], auto_bind=True)
    except Exception as e:
        print(f"[-] Erreur de connexion à l'annuaire ({server_url}) : {e}")
        sys.exit(1)
        
    print(f"[+] Connecté à l'annuaire en tant que {config['BIND_USER']}")
    
    # 1. Créer l'unité organisationnelle pour les utilisateurs et groupes si non existants
    user_ou = config['USER_OU']
    group_ou = config['GROUP_OU']
    
    ous = [user_ou, group_ou]
    for ou_dn in ous:
        # Extraire le premier composant RDN de l'OU
        parts = ou_dn.split(',')
        rdn_parts = parts[0].split('=')
        if len(rdn_parts) == 2:
            attr_type = rdn_parts[0]
            attr_val = rdn_parts[1]
            try:
                conn.add(ou_dn, object_class=['organizationalUnit', 'top'], attributes={attr_type: attr_val})
                print(f"  [+] OU créée : {ou_dn}")
            except Exception as e:
                if 'entryAlreadyExists' in str(e):
                    print(f"  [.] OU existe déjà : {ou_dn}")
                else:
                    print(f"  [-] Erreur OU {ou_dn} : {e}")

    # 2. Créer les groupes selon le type de serveur
    groups_cn = ['managers', 'admins', 'employes']
    for cn in groups_cn:
        if server_type == 'ACTIVE_DIRECTORY':
            dn = f"CN={cn},{group_ou}"
            obj_classes = ['group', 'top']
        else:
            dn = f"cn={cn},{group_ou}"
            obj_classes = ['groupOfNames', 'top']
            
        try:
            # Pour satisfaire le schéma groupOfNames d'OpenLDAP, on ajoute le bind_user comme membre initial
            attrs = {
                'cn': cn,
                'member': config['BIND_USER']
            }
            conn.add(dn, object_class=obj_classes, attributes=attrs)
            print(f"  [+] Groupe créé : {dn}")
        except Exception as e:
            if 'entryAlreadyExists' in str(e):
                print(f"  [.] Groupe existe déjà : {dn}")
            else:
                print(f"  [-] Erreur groupe {dn} : {e}")

    # 3. Créer les utilisateurs simulés
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
        if server_type == 'ACTIVE_DIRECTORY':
            dn = f"CN={u['cn']},{user_ou}"
            object_classes = ['top', 'person', 'organizationalPerson', 'user']
            attrs = {
                'cn': u['cn'],
                'sAMAccountName': u['uid'],
                'userPrincipalName': f"{u['uid']}@{config.get('DOMAIN')}",
                'givenName': u['givenName'],
                'sn': u['sn'],
                'mail': u['mail'],
                'department': u['ou'],
                'title': u['role'],
            }
        else: # OPENLDAP
            dn = f"uid={u['uid']},{user_ou}"
            object_classes = ['top', 'person', 'organizationalPerson', 'inetOrgPerson']
            attrs = {
                'cn': u['cn'],
                'sn': u['sn'],
                'givenName': u['givenName'],
                'mail': u['mail'],
                'ou': u['ou'],
                'title': u['role'],
                'userPassword': u['password']
            }
        
        # Supprimer si existant pour repartir sur une base propre
        try:
            if server_type == 'ACTIVE_DIRECTORY':
                conn.search(config['BASE_DN'], f'(sAMAccountName={u["uid"]})')
            else:
                conn.search(config['BASE_DN'], f'(uid={u["uid"]})')
                
            if conn.entries:
                existing_dn = conn.entries[0].entry_dn
                conn.delete(existing_dn)
                print(f"  [-] Supprimé utilisateur existant : {existing_dn}")
        except Exception:
            pass

        try:
            res = conn.add(dn, object_class=object_classes, attributes=attrs)
            if res:
                print(f"  [+] Utilisateur créé : {dn} (Rôle: {u['role']})")
                
                # Établir mot de passe et activer pour AD
                if server_type == 'ACTIVE_DIRECTORY':
                    if use_ssl or conn.server.ssl:
                        unicode_pwd = f'"{u["password"]}"'.encode('utf-16-le')
                        conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [unicode_pwd])]})
                        print(f"    [+] Mot de passe AD défini.")
                    else:
                        print(f"    [!] Warning: Mot de passe non défini pour AD (liaison non sécurisée).")
                    
                    # Activer le compte AD (512 = NORMAL_ACCOUNT)
                    conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [512])]})
                    print(f"    [+] Compte AD activé.")
                
                # Ajouter aux groupes
                g_cn = 'managers' if u['role'] == 'MANAGER' else 'admins' if u['role'] == 'ADMIN' else 'employes'
                group_dn = f"CN={g_cn},{group_ou}" if server_type == 'ACTIVE_DIRECTORY' else f"cn={g_cn},{group_ou}"
                
                try:
                    conn.modify(group_dn, {'member': [(MODIFY_ADD, [dn])]})
                    print(f"    [+] Ajouté au groupe {g_cn}")
                except Exception as ex:
                    print(f"    [-] Erreur ajout groupe {g_cn} : {ex}")
            else:
                print(f"  [-] Échec création {u['uid']} : {conn.result.get('description')}")
        except Exception as e:
            print(f"  [-] Erreur utilisateur {dn} : {e}")

    # Recherche de vérification
    print("[+] Recherche de vérification...")
    if server_type == 'ACTIVE_DIRECTORY':
        conn.search(config['BASE_DN'], '(objectClass=user)', attributes=['cn', 'mail', 'department', 'title'])
    else:
        conn.search(config['BASE_DN'], '(objectClass=inetOrgPerson)', attributes=['cn', 'mail', 'ou', 'title'])
        
    for entry in conn.entries:
        dept_val = entry.department.value if hasattr(entry, 'department') else entry.ou.value if hasattr(entry, 'ou') else 'Inconnue'
        print(f"  [V] Trouvé : {entry.cn} ({entry.mail}) dans {dept_val} (Rôle: {entry.title})")

    print("\n[SUCCESS] L'annuaire a été peuplé avec succès.")

if __name__ == "__main__":
    seed_ldap()
