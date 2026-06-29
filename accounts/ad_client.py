import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

# Importer ldap3 optionnellement pour éviter des plantages au démarrage si absent
try:
    import ldap3
    from ldap3 import Server, Connection, ALL, SUBTREE, BASE, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
    from ldap3.core.exceptions import (
        LDAPException,
        LDAPBindError,
        LDAPInsufficientAccessRightsResult
    )
    LDAP3_AVAILABLE = True
except ImportError as e:
    LDAP3_AVAILABLE = False
    logger.error(f"La bibliothèque 'ldap3' n'est pas installée ou est incomplète. Détail : {e}")

class ADClientException(Exception):
    """Exception de base pour les erreurs ADClient."""
    pass

class ADClientPermissionException(ADClientException):
    """Exception levée en cas de privilèges insuffisants (délégation)."""
    pass

class ADClientSecurityException(ADClientException):
    """Exception levée en cas de contraintes de sécurité non respectées (ex: pas de SSL)."""
    pass


class ADClient:
    def __init__(self):
        self.config = getattr(settings, 'ACTIVE_DIRECTORY', {})
        self.server_type = self.config.get('SERVER_TYPE', 'ACTIVE_DIRECTORY').upper()
        self.mock_mode = self.config.get('MOCK_MODE', False)
        
        # En mode simulation (Mock), on stocke les utilisateurs en mémoire pour la session
        if self.mock_mode:
            self.mock_users = self.config.get('MOCK_USERS', {})
            logger.info("ADClient initialisé en MODE SIMULATION (MOCK)")
        else:
            logger.info(f"ADClient initialisé en MODE RÉEL ({self.server_type})")

    def is_enabled(self):
        """Indique si le client AD est utilisable."""
        if self.mock_mode:
            return True
        return LDAP3_AVAILABLE

    def _get_server(self):
        """Crée et retourne l'objet Server ldap3."""
        if not self.is_enabled():
            raise ADClientException("ldap3 n'est pas installé ou client non activé.")
        
        server_url = self.config.get('SERVER', 'ldap://localhost:389')
        use_ssl = self.config.get('USE_SSL', False)
        
        # Si l'URL commence par ldaps://, forcer use_ssl à True
        if server_url.startswith('ldaps://'):
            use_ssl = True
            
        try:
            # Récupérer les informations de schéma si requis
            server = Server(
                server_url, 
                use_ssl=use_ssl, 
                get_info=ALL,
                connect_timeout=self.config.get('CONNECTION_TIMEOUT', 5)
            )
            return server
        except Exception as e:
            raise ADClientException(f"Impossible de se connecter au serveur LDAP {server_url} : {e}")

    def _get_admin_connection(self):
        """Établit une connexion avec le compte de service (Admin/Délégation)."""
        if self.mock_mode:
            return None
            
        server = self._get_server()
        bind_user = self.config.get('BIND_USER')
        bind_password = self.config.get('BIND_PASSWORD')
        
        if not bind_user or not bind_password:
            raise ADClientException("Identifiants du compte de service (BIND_USER/BIND_PASSWORD) manquants dans la configuration.")
            
        try:
            conn = Connection(server, user=bind_user, password=bind_password, auto_bind=True)
            return conn
        except LDAPBindError as e:
            raise ADClientPermissionException(
                f"Échec de liaison du compte de service ({bind_user}). Vérifiez les identifiants ou les droits d'accès : {e}"
            )
        except Exception as e:
            raise ADClientException(f"Erreur technique de connexion : {e}")

    def _is_connection_secure(self, conn):
        """Vérifie si la connexion actuelle utilise SSL ou TLS chiffré."""
        if self.mock_mode:
            return True
        if not conn:
            return False
        # Retourne True si SSL est activé ou si TLS StartTLS est en place
        return conn.server.ssl or getattr(conn, 'tls_started', False)

    def _get_user_dn(self, conn, username):
        """Recherche un utilisateur et renvoie son DN exact."""
        if self.mock_mode:
            return f"CN={username},{self.config.get('USER_OU')}"
            
        base_dn = self.config.get('BASE_DN', '')
        
        if self.server_type == 'ACTIVE_DIRECTORY':
            search_filter = f"(|(sAMAccountName={username})(userPrincipalName={username})(mail={username}))"
            search_attrs = ['cn', 'userAccountControl']
        else:
            search_filter = f"(uid={username})"
            search_attrs = ['cn']
            
        try:
            conn.search(base_dn, search_filter, attributes=search_attrs)
            if conn.entries:
                return conn.entries[0].entry_dn
            return None
        except Exception as e:
            logger.error(f"Erreur de recherche utilisateur DN pour {username} : {e}")
            return None

    def authenticate(self, username, password):
        """
        Authentifie un utilisateur en vérifiant ses identifiants.
        Retourne un dictionnaire avec ses attributs ou None si échec.
        """
        username = username.strip().lower()
        if not username or not password:
            return None

        if self.mock_mode:
            if username in self.mock_users:
                user_data = self.mock_users[username]
                if user_data['password'] == password:
                    return {
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'email': user_data['email'],
                        'department': user_data['department'],
                        'role': user_data['role'],
                    }
            return None

        # Liaison Admin pour trouver l'utilisateur et récupérer ses attributs
        try:
            admin_conn = self._get_admin_connection()
        except Exception as e:
            logger.error(f"Échec liaison admin pour authentifier {username} : {e}")
            return None

        user_dn = self._get_user_dn(admin_conn, username)
        if not user_dn:
            logger.warning(f"Utilisateur {username} non trouvé dans l'annuaire.")
            admin_conn.unbind()
            return None

        # Lire ses informations
        try:
            if self.server_type == 'ACTIVE_DIRECTORY':
                search_filter = f"(|(sAMAccountName={username})(userPrincipalName={username}))"
                attrs = ['givenName', 'sn', 'mail', 'department', 'ou', 'title', 'memberOf', 'userAccountControl']
            else:
                search_filter = f"(uid={username})"
                attrs = ['givenName', 'sn', 'mail', 'ou', 'title']
                
            admin_conn.search(user_dn, search_filter, search_scope=BASE, attributes=attrs)
            if not admin_conn.entries:
                admin_conn.unbind()
                return None
                
            entry = admin_conn.entries[0]
            
            # Vérifier si le compte est désactivé sous AD
            if self.server_type == 'ACTIVE_DIRECTORY' and hasattr(entry, 'userAccountControl'):
                uac = int(entry.userAccountControl.value or 512)
                if uac & 2: # ACCOUNTDISABLE = 2
                    logger.warning(f"Compte AD désactivé pour {username}")
                    admin_conn.unbind()
                    return None
            
            # Maintenant, essayer de se lier en tant qu'utilisateur pour valider son mot de passe
            server = self._get_server()
            try:
                user_conn = Connection(server, user=user_dn, password=password, auto_bind=True)
                user_conn.unbind()
            except LDAPBindError:
                logger.warning(f"Mot de passe incorrect pour l'utilisateur {username}")
                admin_conn.unbind()
                return None

            # Résoudre le rôle
            role = 'EMPLOYE'
            if hasattr(entry, 'title') and entry.title:
                title_val = str(entry.title).upper()
                if title_val in ['EMPLOYE', 'MANAGER', 'ADMIN']:
                    role = title_val
            elif hasattr(entry, 'memberOf') and entry.memberOf:
                groups = [str(g).lower() for g in entry.memberOf]
                if any('admin' in g for g in groups):
                    role = 'ADMIN'
                elif any('manager' in g or 'directeur' in g for g in groups):
                    role = 'MANAGER'
            else:
                # Fallback recherche de groupes (OpenLDAP ou AD)
                group_ou = self.config.get('GROUP_OU', f"ou=groups,{self.config.get('BASE_DN')}")
                try:
                    admin_conn.search(group_ou, f"(member={user_dn})", attributes=['cn'])
                    user_groups = [str(g.cn).lower() for g in admin_conn.entries]
                    if any('admin' in g for g in user_groups):
                        role = 'ADMIN'
                    elif any('manager' in g for g in user_groups):
                        role = 'MANAGER'
                except Exception as group_err:
                    logger.warning(f"Impossible de vérifier l'appartenance aux groupes : {group_err}")

            # Résoudre la direction / département
            dept = 'Direction Technique'
            if hasattr(entry, 'department') and entry.department:
                dept = str(entry.department)
            elif hasattr(entry, 'ou') and entry.ou:
                if isinstance(entry.ou, list) or hasattr(entry.ou, '__iter__'):
                    dept = str(entry.ou[0]) if entry.ou else 'Direction Technique'
                else:
                    dept = str(entry.ou)

            ad_user_info = {
                'first_name': str(entry.givenName) if hasattr(entry, 'givenName') and entry.givenName else '',
                'last_name': str(entry.sn) if hasattr(entry, 'sn') and entry.sn else '',
                'email': str(entry.mail) if hasattr(entry, 'mail') and entry.mail else f"{username}@{self.config.get('DOMAIN')}",
                'department': dept,
                'role': role,
            }
            admin_conn.unbind()
            return ad_user_info
            
        except Exception as e:
            logger.error(f"Erreur d'authentification AD pour {username} : {e}")
            return None

    def create_user(self, user, password):
        """Créer un utilisateur dans l'annuaire."""
        if self.mock_mode:
            self.mock_users[user.username] = {
                'password': password,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'department': user.direction.nom if user.direction else 'Direction Générale',
                'role': user.role,
            }
            logger.info(f"[MOCK AD] Utilisateur créé : {user.username}")
            return True

        conn = self._get_admin_connection()
        user_ou = self.config.get('USER_OU')
        domain = self.config.get('DOMAIN')
        
        # Format informatif CN=Prénom Nom si possible, sinon CN=username
        if user.first_name and user.last_name:
            cn_value = f"{user.first_name} {user.last_name}"
        else:
            cn_value = user.username
            
        if self.server_type == 'ACTIVE_DIRECTORY':
            dn = f"CN={cn_value},{user_ou}"
            object_classes = ['top', 'person', 'organizationalPerson', 'user']
            attrs = {
                'cn': cn_value,
                'sAMAccountName': user.username,
                'userPrincipalName': f"{user.username}@{domain}",
                'givenName': user.first_name or '',
                'sn': user.last_name or '',
                'mail': user.email or '',
                'department': user.direction.nom if user.direction else '',
                'title': user.role,
            }
        else: # OPENLDAP
            dn = f"uid={user.username},{user_ou}"
            object_classes = ['top', 'person', 'organizationalPerson', 'inetOrgPerson']
            attrs = {
                'cn': cn_value,
                'sn': user.last_name or user.username,
                'givenName': user.first_name or '',
                'mail': user.email or '',
                'ou': user.direction.nom if user.direction else '',
                'title': user.role,
                'userPassword': password
            }

        try:
            # 1. Ajouter l'utilisateur
            res = conn.add(dn, object_class=object_classes, attributes=attrs)
            if not res:
                # Si l'ajout échoue en raison de droits insuffisants
                if conn.result.get('result') == 50: # Insufficient access rights
                    raise ADClientPermissionException(
                        "Droits d'écriture AD insuffisants pour le compte de service lors de la création."
                    )
                raise ADClientException(f"Échec de la création AD : {conn.result.get('description')}")
                
            # 2. Configurer le mot de passe (AD requiert une étape supplémentaire sécurisée)
            if self.server_type == 'ACTIVE_DIRECTORY':
                if not self._is_connection_secure(conn):
                    # Supprimer le compte créé à moitié pour rester propre si requis par config
                    conn.delete(dn)
                    raise ADClientSecurityException(
                        "Impossible de définir le mot de passe AD : la connexion n'est pas sécurisée (SSL/TLS obligatoire pour AD)."
                    )
                
                # Format requis pour AD unicodePwd : UTF-16LE entouré de guillemets doubles
                unicode_pwd = f'"{password}"'.encode('utf-16-le')
                conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [unicode_pwd])]})
                if conn.result.get('result') != 0:
                    conn.delete(dn)
                    raise ADClientException(f"Impossible de définir le mot de passe AD : {conn.result.get('description')}")
                
                # Activer le compte AD (512 = NORMAL_ACCOUNT)
                conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [512])]})
                
            # 3. Gérer les groupes de rôles
            self._sync_user_groups(conn, dn, user.role)
            
            logger.info(f"Utilisateur {user.username} créé avec succès dans l'annuaire AD/LDAP.")
            conn.unbind()
            return True
            
        except LDAPInsufficientAccessRightsResult as e:
            raise ADClientPermissionException(f"Droits d'écriture AD insuffisants pour le compte de service : {e}")
        except Exception as e:
            if not isinstance(e, ADClientException):
                raise ADClientException(f"Erreur lors de la création dans l'annuaire : {e}")
            raise e

    def update_user(self, user, password=None):
        """Mettre à jour les informations d'un utilisateur existant."""
        if self.mock_mode:
            if user.username in self.mock_users:
                self.mock_users[user.username]['first_name'] = user.first_name
                self.mock_users[user.username]['last_name'] = user.last_name
                self.mock_users[user.username]['email'] = user.email
                self.mock_users[user.username]['department'] = user.direction.nom if user.direction else 'Direction Générale'
                self.mock_users[user.username]['role'] = user.role
                if password:
                    self.mock_users[user.username]['password'] = password
                logger.info(f"[MOCK AD] Utilisateur mis à jour : {user.username}")
                return True
            return False

        conn = self._get_admin_connection()
        user_dn = self._get_user_dn(conn, user.username)
        if not user_dn:
            raise ADClientException(f"Utilisateur {user.username} introuvable dans l'annuaire.")

        modifications = {}
        if self.server_type == 'ACTIVE_DIRECTORY':
            modifications.update({
                'givenName': [(MODIFY_REPLACE, [user.first_name or ''])],
                'sn': [(MODIFY_REPLACE, [user.last_name or ''])],
                'mail': [(MODIFY_REPLACE, [user.email or ''])],
                'department': [(MODIFY_REPLACE, [user.direction.nom if user.direction else ''])],
                'title': [(MODIFY_REPLACE, [user.role])],
            })
        else: # OPENLDAP
            modifications.update({
                'givenName': [(MODIFY_REPLACE, [user.first_name or ''])],
                'sn': [(MODIFY_REPLACE, [user.last_name or user.username])],
                'mail': [(MODIFY_REPLACE, [user.email or ''])],
                'ou': [(MODIFY_REPLACE, [user.direction.nom if user.direction else ''])],
                'title': [(MODIFY_REPLACE, [user.role])],
            })

        # Mettre à jour le mot de passe si fourni
        if password:
            if self.server_type == 'ACTIVE_DIRECTORY':
                if not self._is_connection_secure(conn):
                    raise ADClientSecurityException(
                        "Impossible de modifier le mot de passe AD : la connexion n'est pas sécurisée (SSL/TLS requis)."
                    )
                unicode_pwd = f'"{password}"'.encode('utf-16-le')
                modifications['unicodePwd'] = [(MODIFY_REPLACE, [unicode_pwd])]
            else:
                modifications['userPassword'] = [(MODIFY_REPLACE, [password])]

        try:
            res = conn.modify(user_dn, modifications)
            if not res:
                if conn.result.get('result') == 50:
                    raise ADClientPermissionException("Droits d'écriture AD insuffisants pour modifier cet utilisateur.")
                raise ADClientException(f"Échec de mise à jour AD : {conn.result.get('description')}")
                
            # Mettre à jour le groupe si requis
            self._sync_user_groups(conn, user_dn, user.role)
            
            logger.info(f"Utilisateur {user.username} mis à jour avec succès dans l'annuaire.")
            conn.unbind()
            return True
        except Exception as e:
            if not isinstance(e, ADClientException):
                raise ADClientException(f"Erreur de modification dans l'annuaire : {e}")
            raise e

    def toggle_user_status(self, username, is_active):
        """Activer ou désactiver un utilisateur."""
        if self.mock_mode:
            logger.info(f"[MOCK AD] Utilisateur {username} changé d'état : actif={is_active}")
            return True

        if self.server_type != 'ACTIVE_DIRECTORY':
            # OpenLDAP ne supporte pas nativement userAccountControl
            logger.info(f"Désactivation AD ignorée pour OpenLDAP pour {username}.")
            return True

        conn = self._get_admin_connection()
        user_dn = self._get_user_dn(conn, username)
        if not user_dn:
            raise ADClientException(f"Utilisateur {username} introuvable dans l'annuaire.")

        try:
            # Récupérer la valeur actuelle de userAccountControl
            conn.search(user_dn, f"(sAMAccountName={username})", search_scope=BASE, attributes=['userAccountControl'])
            if not conn.entries:
                raise ADClientException("Impossible de lire les attributs de compte.")
                
            entry = conn.entries[0]
            current_uac = int(entry.userAccountControl.value or 512)
            
            # Bitwise 2 = ACCOUNTDISABLE
            if is_active:
                new_uac = current_uac & ~2
            else:
                new_uac = current_uac | 2
                
            conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [new_uac])]})
            if conn.result.get('result') != 0:
                if conn.result.get('result') == 50:
                    raise ADClientPermissionException("Droits insuffisants pour changer le statut d'activation du compte.")
                raise ADClientException(f"Impossible de mettre à jour userAccountControl : {conn.result.get('description')}")
                
            logger.info(f"État utilisateur {username} mis à jour dans AD : actif={is_active} (UAC: {new_uac})")
            conn.unbind()
            return True
        except Exception as e:
            if not isinstance(e, ADClientException):
                raise ADClientException(f"Erreur lors du changement de statut d'activité dans l'annuaire : {e}")
            raise e

    def delete_user(self, username):
        """Supprimer définitivement un utilisateur de l'annuaire."""
        if self.mock_mode:
            if username in self.mock_users:
                del self.mock_users[username]
            logger.info(f"[MOCK AD] Utilisateur supprimé : {username}")
            return True

        conn = self._get_admin_connection()
        user_dn = self._get_user_dn(conn, username)
        if not user_dn:
            logger.warning(f"Tentative de suppression de {username} introuvable dans l'annuaire.")
            conn.unbind()
            return False

        try:
            res = conn.delete(user_dn)
            if not res:
                if conn.result.get('result') == 50:
                    raise ADClientPermissionException("Droits d'écriture AD insuffisants pour supprimer cet utilisateur.")
                raise ADClientException(f"Échec de suppression AD : {conn.result.get('description')}")
                
            logger.info(f"Utilisateur {username} supprimé de l'annuaire AD/LDAP.")
            conn.unbind()
            return True
        except Exception as e:
            if not isinstance(e, ADClientException):
                raise ADClientException(f"Erreur de suppression dans l'annuaire : {e}")
            raise e

    def _sync_user_groups(self, conn, user_dn, role):
        """Associe l'utilisateur au groupe correspondant à son rôle et le retire des autres."""
        group_ou = self.config.get('GROUP_OU')
        
        # Mappage des rôles OPALE vers les CN de groupes AD
        role_groups = {
            'ADMIN': 'admins',
            'MANAGER': 'managers',
            'EMPLOYE': 'employes'
        }
        
        target_group_cn = role_groups.get(role)
        if not target_group_cn:
            return

        for r, g_cn in role_groups.items():
            group_dn = f"CN={g_cn},{group_ou}" if self.server_type == 'ACTIVE_DIRECTORY' else f"cn={g_cn},{group_ou}"
            
            try:
                if r == role:
                    # Ajouter au groupe cible
                    conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]})
                else:
                    # Retirer des autres groupes
                    conn.modify(group_dn, {'member': [(MODIFY_DELETE, [user_dn])]})
            except Exception as e:
                # Ignorer si le groupe n'existe pas ou si l'utilisateur n'en fait déjà pas partie
                # ou s'il s'agit du membre initial.
                logger.debug(f"Modification groupe {group_dn} pour {user_dn} : {e}")


_ad_client_instance = None

def get_ad_client():
    """Singleton helper pour obtenir l'instance unique d'ADClient."""
    global _ad_client_instance
    if _ad_client_instance is None:
        _ad_client_instance = ADClient()
    return _ad_client_instance
