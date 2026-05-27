"""
accounts/views.py
Views for the OPALE Service Hub — User features:
  - annuaire_view        : Company directory with search/filter
  - profile_view         : Update name & email
  - change_password_view : Secure password change
  - gestion_users_*      : Admin CRUD for user management (staff only)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db.models import Q

from .models import Utilisateur
from .forms import ProfilForm, OpalePasswordChangeForm, UtilisateurAdminForm
from organizations.models import Direction
from audit.logic import log_activite

staff_required = user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')


# ---------------------------------------------------------------------------
# Annuaire d'Entreprise
# ---------------------------------------------------------------------------

@login_required
def annuaire_view(request):
    """
    Affiche la liste de tous les employés de l'ART.
    Supporte une recherche par nom (GET param: q) et un filtre par direction.
    """
    query = request.GET.get('q', '').strip()
    direction_id = request.GET.get('direction', '')

    employes = Utilisateur.objects.filter(is_active=True).select_related('direction')

    if query:
        employes = employes.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
        )

    if direction_id:
        employes = employes.filter(direction_id=direction_id)

    employes = employes.order_by('last_name', 'first_name')
    directions = Direction.objects.all().order_by('nom')

    return render(request, 'accounts/annuaire.html', {
        'employes': employes,
        'directions': directions,
        'query': query,
        'selected_direction': direction_id,
    })


# ---------------------------------------------------------------------------
# Gestion du Profil
# ---------------------------------------------------------------------------

@login_required
def profile_view(request):
    """
    Vue principale du profil utilisateur.
    Affiche et traite le formulaire de mise à jour des infos personnelles.
    """
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_activite(request, "Mise à jour du profil", {
                "champs": list(form.changed_data)
            })
            messages.success(request, "✅ Votre profil a été mis à jour avec succès.")
            return redirect('profile')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ProfilForm(instance=request.user)

    pw_form = OpalePasswordChangeForm(user=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'pw_form': pw_form,
    })


@login_required
def change_password_view(request):
    """
    Traite uniquement le changement de mot de passe (POST uniquement).
    Redirige vers le profil avec un message de confirmation.
    """
    if request.method == 'POST':
        pw_form = OpalePasswordChangeForm(user=request.user, data=request.POST)
        if pw_form.is_valid():
            pw_form.save()
            update_session_auth_hash(request, pw_form.user)
            log_activite(request, "Changement de mot de passe")
            messages.success(request, "🔐 Mot de passe modifié avec succès.")
            return redirect('profile')
        else:
            form = ProfilForm(instance=request.user)
            messages.error(request, "Erreur dans le formulaire de mot de passe.")
            return render(request, 'accounts/profile.html', {
                'form': form,
                'pw_form': pw_form,
            })

    return redirect('profile')


# ---------------------------------------------------------------------------
# Gestion des Utilisateurs (Admin CRUD) — staff only
# ---------------------------------------------------------------------------

@staff_required
@login_required
def gestion_users_list(request):
    """Liste tous les utilisateurs avec recherche et filtres."""
    query = request.GET.get('q', '').strip()
    direction_id = request.GET.get('direction', '')
    role_filter = request.GET.get('role', '')

    users = Utilisateur.objects.select_related('direction').order_by('last_name', 'first_name')

    if query:
        users = users.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
            | Q(email__icontains=query)
        )
    if direction_id:
        users = users.filter(direction_id=direction_id)
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'accounts/admin/users_list.html', {
        'users': users,
        'directions': Direction.objects.all().order_by('nom'),
        'role_choices': Utilisateur.ROLE_CHOICES,
        'query': query,
        'selected_direction': direction_id,
        'selected_role': role_filter,
    })


@staff_required
@login_required
def gestion_users_create(request):
    """Créer un nouvel utilisateur."""
    if request.method == 'POST':
        form = UtilisateurAdminForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activite(request, f"Création utilisateur : {user.username}", {"user_id": user.id})
            messages.success(request, f"✅ Utilisateur « {user.get_full_name() or user.username} » créé avec succès.")
            return redirect('gestion_users_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = UtilisateurAdminForm()

    return render(request, 'accounts/admin/user_form.html', {
        'form': form,
        'action': 'Créer',
        'page_title': 'Nouvel utilisateur',
    })


@staff_required
@login_required
def gestion_users_edit(request, user_id):
    """Modifier un utilisateur existant."""
    user_obj = get_object_or_404(Utilisateur, pk=user_id)

    if request.method == 'POST':
        form = UtilisateurAdminForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            log_activite(request, f"Modification utilisateur : {user_obj.username}", {"user_id": user_obj.id})
            messages.success(request, f"✅ Utilisateur « {user_obj.get_full_name() or user_obj.username} » modifié.")
            return redirect('gestion_users_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = UtilisateurAdminForm(instance=user_obj)

    return render(request, 'accounts/admin/user_form.html', {
        'form': form,
        'user_obj': user_obj,
        'action': 'Modifier',
        'page_title': f'Modifier — {user_obj.get_full_name() or user_obj.username}',
    })


@staff_required
@login_required
def gestion_users_toggle(request, user_id):
    """Activer / désactiver un compte (POST only)."""
    if request.method == 'POST':
        user_obj = get_object_or_404(Utilisateur, pk=user_id)
        if user_obj == request.user:
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
            return redirect('gestion_users_list')
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        action = "Activation" if user_obj.is_active else "Désactivation"
        log_activite(request, f"{action} utilisateur : {user_obj.username}", {"user_id": user_obj.id})
        status = "activé" if user_obj.is_active else "désactivé"
        messages.success(request, f"Compte de {user_obj.username} {status}.")
    return redirect('gestion_users_list')


@staff_required
@login_required
def gestion_users_delete(request, user_id):
    """Supprimer définitivement un utilisateur (POST confirmation)."""
    user_obj = get_object_or_404(Utilisateur, pk=user_id)
    if user_obj == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('gestion_users_list')

    if request.method == 'POST':
        username = user_obj.username
        log_activite(request, f"Suppression utilisateur : {username}", {"user_id": user_obj.id})
        user_obj.delete()
        messages.success(request, f"Utilisateur « {username} » supprimé définitivement.")
        return redirect('gestion_users_list')

    return render(request, 'accounts/admin/user_confirm_delete.html', {'user_obj': user_obj})


# ---------------------------------------------------------------------------
# SINGLE SIGN-ON (SSO) SERVICES
# ---------------------------------------------------------------------------
from django.core import signing
from django.http import JsonResponse

def sso_authorize_view(request):
    """
    Point d'entrée d'autorisation de l'Identity Provider (IdP).
    Génère un jeton SSO signé cryptographiquement (valable 60s)
    et redirige l'utilisateur authentifié vers le callback de l'application (SP).
    """
    if not request.user.is_authenticated:
        # Enregistrer les paramètres de requête pour y revenir après connexion
        login_url = '/accounts/login/'
        query = request.GET.urlencode()
        next_url = f"{request.path}?{query}" if query else request.path
        return redirect(f"{login_url}?next={next_url}")

    app_id = request.GET.get('app', 'default')
    next_param = request.GET.get('next', '')

    if not next_param:
        return redirect('dashboard')

    # Générer le payload du jeton SSO
    payload = {
        'username': request.user.username,
        'app': app_id,
    }
    
    signer = signing.TimestampSigner()
    token = signer.sign_object(payload)

    # Consigner la génération du jeton dans l'audit d'Opale
    log_activite(
        request,
        f"Génération Jeton SSO — Application : {app_id}",
        {
            "username": request.user.username,
            "app_id": app_id,
            "redirect_to": next_param
        }
    )

    # Rediriger vers l'application cliente avec le jeton
    connector = '&' if '?' in next_param else '?'
    redirect_url = f"{next_param}{connector}token={token}"
    return redirect(redirect_url)


def sso_verify_view(request):
    """
    API REST de vérification de jeton SSO.
    Appelée par les applications clientes (Service Providers) pour valider
    un jeton reçu et obtenir le profil complet de l'utilisateur.
    """
    token = request.GET.get('token')
    if not token:
        return JsonResponse({'valid': False, 'error': 'Jeton manquant'}, status=400)

    signer = signing.TimestampSigner()
    try:
        # Décrypter et vérifier l'expiration du jeton (max 60 secondes)
        payload = signer.unsign_object(token, max_age=60)
        username = payload.get('username')
        
        # Récupérer l'utilisateur correspondant
        user = Utilisateur.objects.select_related('direction').get(username=username)
        
        # Enregistrer la validation de jeton réussie dans les logs d'activité
        log_activite(
            request,
            f"Validation Jeton SSO — Utilisateur : {username}",
            {
                "username": username,
                "app": payload.get('app'),
                "status": "success"
            }
        )
        
        return JsonResponse({
            'valid': True,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.role,
            'direction': user.direction.nom if user.direction else 'Direction Générale',
            'direction_code': user.direction.code if user.direction else 'DG'
        })
    except signing.SignatureExpired:
        return JsonResponse({'valid': False, 'error': 'Le jeton SSO a expiré (durée max: 60s)'}, status=400)
    except signing.BadSignature:
        return JsonResponse({'valid': False, 'error': 'Signature de jeton invalide'}, status=400)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Utilisateur introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)}, status=500)

