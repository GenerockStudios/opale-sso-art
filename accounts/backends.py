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

        from accounts.ad_client import get_ad_client
        client = get_ad_client()
        
        ad_user_info = None
        if client.is_enabled():
            ad_user_info = client.authenticate(username, password)
        else:
            logger.error("ADClient n'est pas activé ou la bibliothèque ldap3 est manquante.")
            if request:
                log_activite(
                    request,
                    "Erreur Connexion AD (ADClient inactif)",
                    {"error": "ADClient is not enabled or ldap3 missing."}
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
