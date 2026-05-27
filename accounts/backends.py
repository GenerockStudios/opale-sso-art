import logging
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.db import transaction
from accounts.models import Utilisateur
from organizations.models import Direction
from audit.logic import log_activite

logger = logging.getLogger(__name__)

class ActiveDirectoryBackend(BaseBackend):
    """
    Backend d'authentification pour Active Directory.
    Prend en charge une liaison LDAP réelle (via la bibliothèque ldap3)
    et une simulation (Mock) pour la démonstration du PoC.
    
    Synchronise automatiquement le profil de l'employé, son rôle et
    sa Direction d'appartenance avec la base de données locale d'OPALE.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # Normaliser l'identifiant en minuscules
        username = username.strip().lower()

        ad_config = getattr(settings, 'ACTIVE_DIRECTORY', {})
        mock_mode = ad_config.get('MOCK_MODE', True)
        
        ad_user_info = None

        if mock_mode:
            # ─── MODE SIMULATION (MOCK) ───
            mock_users = ad_config.get('MOCK_USERS', {})
            if username in mock_users:
                user_data = mock_users[username]
                if user_data['password'] == password:
                    ad_user_info = {
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'email': user_data['email'],
                        'department': user_data['department'],
                        'role': user_data['role'],
                    }
        else:
            # ─── MODE RÉEL (LDAP / Active Directory) ───
            try:
                import ldap3
                from ldap3 import Server, Connection, ALL
                
                server_url = ad_config.get('SERVER', 'ldap://localhost')
                domain = ad_config.get('DOMAIN', 'art.cm')
                base_dn = ad_config.get('BASE_DN', 'dc=art,dc=cm')
                
                server = Server(server_url, get_info=ALL)
                
                # 1. Tentatives de liaison LDAP (Bind)
                conn = None
                bind_dn = None
                
                # Option A: Liaison Active Directory standard (UPN: username@domain)
                try:
                    user_principal = f"{username}@{domain}"
                    conn = Connection(server, user=user_principal, password=password, auto_bind=True)
                    bind_dn = user_principal
                except Exception as e:
                    logger.debug(f"Échec liaison UPN AD pour {username}: {e}")
                
                # Option B: Liaison standard OpenLDAP (DN: uid=username,ou=users,base_dn)
                if not conn:
                    try:
                        user_dn = f"uid={username},ou=users,{base_dn}"
                        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
                        bind_dn = user_dn
                    except Exception as e:
                        logger.debug(f"Échec liaison DN standard pour {username}: {e}")
                
                if not conn:
                    # Échec de liaison pour tous les modes
                    return None

                # 2. Recherche des informations utilisateur (Filtre hybride AD/OpenLDAP)
                search_success = False
                try:
                    search_filter = f"(|(sAMAccountName={username})(uid={username}))"
                    conn.search(
                        base_dn, 
                        search_filter, 
                        attributes=['givenName', 'sn', 'mail', 'department', 'ou', 'title', 'memberOf']
                    )
                    if conn.entries:
                        search_success = True
                except Exception as search_err:
                    logger.debug(f"Erreur recherche AD: {search_err}")

                # Repli sur recherche standard OpenLDAP (BASE sur DN de l'utilisateur) si échec ou aucun résultat
                if not search_success:
                    try:
                        search_base = bind_dn if (bind_dn and ',' in bind_dn) else f"uid={username},ou=users,{base_dn}"
                        from ldap3 import BASE
                        conn.search(
                            search_base, 
                            f"(uid={username})", 
                            search_scope=BASE,
                            attributes=['givenName', 'sn', 'mail', 'ou', 'title']
                        )
                    except Exception as fallback_err:
                        logger.error(f"Échec recherche LDAP repli pour {username}: {fallback_err}")
                        return None
                
                if conn.entries:
                    entry = conn.entries[0]
                    
                    # 3. Récupération du rôle
                    role = 'EMPLOYE'
                    # Vérifier d'abord si l'attribut title contient un rôle valide (ex: MANAGER)
                    if hasattr(entry, 'title') and entry.title:
                        title_val = str(entry.title).upper()
                        if title_val in ['EMPLOYE', 'MANAGER', 'ADMIN']:
                            role = title_val
                    # Sinon vérifier l'attribut memberOf
                    elif hasattr(entry, 'memberOf') and entry.memberOf:
                        groups = [str(g).lower() for g in entry.memberOf]
                        if any('admin' in g for g in groups):
                            role = 'ADMIN'
                        elif any('manager' in g or 'directeur' in g for g in groups):
                            role = 'MANAGER'
                    # Sinon interroger directement les groupes où l'utilisateur est membre
                    else:
                        try:
                            # dn de l'utilisateur
                            u_dn = entry.entry_dn
                            conn.search(
                                f"ou=groups,{base_dn}",
                                f"(member={u_dn})",
                                attributes=['cn']
                            )
                            user_groups = [str(g.cn).lower() for g in conn.entries]
                            if any('admin' in g for g in user_groups):
                                role = 'ADMIN'
                            elif any('manager' in g for g in user_groups):
                                role = 'MANAGER'
                        except Exception as group_err:
                            logger.warning(f"Impossible de vérifier l'appartenance aux groupes de {username}: {group_err}")
                    
                    # 4. Récupération du département / de la Direction
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
                        'email': str(entry.mail) if hasattr(entry, 'mail') and entry.mail else f"{username}@{domain}",
                        'department': dept,
                        'role': role,
                    }
            except ImportError:
                logger.error("La bibliothèque 'ldap3' n'est pas installée. Impossible de se connecter à Active Directory en mode réel.")
                if request:
                    log_activite(
                        request,
                        "Erreur Connexion AD (ldap3 manquant)",
                        {"error": "ldap3 module not found. Please install requirements."}
                    )
            except Exception as e:
                logger.error(f"Échec de l'authentification Active Directory pour {username} : {e}")
                if request:
                    log_activite(
                        request,
                        "Échec Connexion AD (Technique)",
                        {"username": username, "error": str(e)}
                    )

        # Si l'authentification AD a réussi, on synchronise les données
        if ad_user_info:
            return self._sync_user_data(request, username, ad_user_info)

        return None

    def _sync_user_data(self, request, username, ad_user_info):
        """
        Synchronise de manière atomique l'utilisateur et sa Direction dans Django.
        """
        try:
            with transaction.atomic():
                dept_name = ad_user_info['department']
                
                # 1. Rechercher ou créer la Direction correspondante
                # On génère un code court à partir des initiales si la direction n'existe pas
                words = [w for w in dept_name.split() if w[0].isalpha()]
                derived_code = "".join([w[0].upper() for w in words])[:10]
                if not derived_code:
                    derived_code = "DIR"
                
                direction, created_dir = Direction.objects.get_or_create(
                    nom=dept_name,
                    defaults={
                        'code': derived_code,
                        'description': f"Direction créée automatiquement par import Active Directory pour '{dept_name}'."
                    }
                )
                
                # 2. Rechercher ou créer l'Utilisateur
                user, created_user = Utilisateur.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': ad_user_info['first_name'],
                        'last_name': ad_user_info['last_name'],
                        'email': ad_user_info['email'],
                        'role': ad_user_info['role'],
                        'direction': direction,
                        'is_active': True,
                    }
                )
                
                # Mettre à jour les informations si l'utilisateur existait déjà
                if not created_user:
                    user.first_name = ad_user_info['first_name']
                    user.last_name = ad_user_info['last_name']
                    user.email = ad_user_info['email']
                    user.role = ad_user_info['role']
                    user.direction = direction
                    user.save()

                # 3. Journaliser le succès
                if request:
                    action_title = "Synchronisation Active Directory réussie"
                    log_activite(
                        request, 
                        f"{action_title} - {user.username}", 
                        {
                            "username": username,
                            "direction": dept_name,
                            "role": user.role,
                            "compte_cree": created_user
                        }
                    )
                
                return user
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation locale du compte AD {username} : {e}")
            return None

    def get_user(self, user_id):
        try:
            return Utilisateur.objects.get(pk=user_id)
        except Utilisateur.DoesNotExist:
            return None
