"""
catalogue/views.py
Views for the OPALE Service Hub — App catalogue:
  - DashboardView        : Filtered app grid by user direction
  - launch_app           : Intercept + log + redirect to external app
  - gestion_apps_*       : Admin CRUD for application management (staff only)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Application, DirectionApplication
from .forms import ApplicationForm
from organizations.models import Direction
from audit.logic import log_activite

staff_required = user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')


# ---------------------------------------------------------------------------
# Employee Dashboard — filtered app grid
# ---------------------------------------------------------------------------

class DashboardView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'dashboard.html'
    context_object_name = 'applications'

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.direction:
            return Application.objects.filter(
                directions_autorisees=user.direction,
                est_actif=True
            ).distinct()
        return Application.objects.none()


# ---------------------------------------------------------------------------
# Launch App — access control + audit log
# ---------------------------------------------------------------------------

@login_required
def launch_app(request, app_id):
    """
    Intercepts app launches, verifies direction-level access,
    logs the event (with IP), and redirects to the external URL.
    """
    application = get_object_or_404(Application, id=app_id)

    if request.user.direction and request.user.direction in application.directions_autorisees.all():
        log_activite(request, f"Accès Logiciel : {application.nom}", {
            "app_id": application.id,
            "app_url": application.url_acces,
            "user_agent": request.META.get('HTTP_USER_AGENT', 'N/A'),
        })
        return redirect(application.url_acces)

    log_activite(request, f"Accès REFUSÉ : {application.nom}", {
        "app_id": application.id,
        "reason": "Direction non habilitée",
    })
    return redirect('dashboard')


# ---------------------------------------------------------------------------
# Gestion Applications (Admin CRUD) — staff only
# ---------------------------------------------------------------------------

@staff_required
@login_required
def gestion_apps_list(request):
    """Liste toutes les applications avec filtres."""
    query = request.GET.get('q', '').strip()
    apps = Application.objects.prefetch_related('directions_autorisees').order_by('nom')

    if query:
        apps = apps.filter(nom__icontains=query)

    return render(request, 'catalogue/admin/apps_list.html', {
        'apps': apps,
        'query': query,
    })


@staff_required
@login_required
def gestion_apps_create(request):
    """Créer une nouvelle application avec ses habilitations."""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save()
            # Set M2M directions via DirectionApplication through table
            directions = form.cleaned_data.get('directions', [])
            for direction in directions:
                DirectionApplication.objects.get_or_create(direction=direction, application=app)
            log_activite(request, f"Création application : {app.nom}", {"app_id": app.id})
            messages.success(request, f"✅ Application « {app.nom} » créée avec succès.")
            return redirect('gestion_apps_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ApplicationForm()

    return render(request, 'catalogue/admin/app_form.html', {
        'form': form,
        'action': 'Créer',
        'page_title': 'Nouvelle application',
    })


@staff_required
@login_required
def gestion_apps_edit(request, app_id):
    """Modifier une application existante et ses habilitations."""
    app = get_object_or_404(Application, pk=app_id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=app)
        if form.is_valid():
            form.save()
            # Sync directions: clear and re-add
            directions = form.cleaned_data.get('directions', [])
            DirectionApplication.objects.filter(application=app).delete()
            for direction in directions:
                DirectionApplication.objects.create(direction=direction, application=app)
            log_activite(request, f"Modification application : {app.nom}", {"app_id": app.id})
            messages.success(request, f"✅ Application « {app.nom} » modifiée.")
            return redirect('gestion_apps_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ApplicationForm(instance=app)

    return render(request, 'catalogue/admin/app_form.html', {
        'form': form,
        'app': app,
        'action': 'Modifier',
        'page_title': f'Modifier — {app.nom}',
    })


@staff_required
@login_required
def gestion_apps_toggle(request, app_id):
    """Activer / désactiver une application (POST only)."""
    if request.method == 'POST':
        app = get_object_or_404(Application, pk=app_id)
        app.est_actif = not app.est_actif
        app.save()
        status = "activée" if app.est_actif else "désactivée"
        log_activite(request, f"Toggle application : {app.nom} → {status}", {"app_id": app.id})
        messages.success(request, f"Application « {app.nom} » {status}.")
    return redirect('gestion_apps_list')


@staff_required
@login_required
def gestion_apps_delete(request, app_id):
    """Supprimer définitivement une application."""
    app = get_object_or_404(Application, pk=app_id)

    if request.method == 'POST':
        nom = app.nom
        log_activite(request, f"Suppression application : {nom}", {"app_id": app.id})
        app.delete()
        messages.success(request, f"Application « {nom} » supprimée.")
        return redirect('gestion_apps_list')

    return render(request, 'catalogue/admin/app_confirm_delete.html', {'app': app})
