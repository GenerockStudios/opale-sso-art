"""
audit/views.py
Admin-only views for OPALE audit system:
  - audit_dashboard : Real-time log monitoring with filters
  - matrix_view     : Direction × Application access rights matrix
  - toggle_habilitation : AJAX endpoint to grant/revoke an access
"""
import json
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import LogActivite
from .logic import log_activite
from catalogue.models import Application, DirectionApplication
from organizations.models import Direction
from accounts.models import Utilisateur


# ---------------------------------------------------------------------------
# Audit Dashboard — Log Monitoring
# ---------------------------------------------------------------------------

@staff_member_required
def audit_dashboard(request):
    """
    Admin-only log monitoring dashboard with:
      - Stat counters (today / 7d / 30d)
      - Filters by user (username) and date range
      - Paginated log table (25 per page)
    """
    now = timezone.now()

    # --- Statistics ---
    count_today = LogActivite.objects.filter(
        cree_le__date=now.date()
    ).count()
    count_7d = LogActivite.objects.filter(
        cree_le__gte=now - timedelta(days=7)
    ).count()
    count_30d = LogActivite.objects.filter(
        cree_le__gte=now - timedelta(days=30)
    ).count()

    # --- Filters ---
    logs = LogActivite.objects.select_related('utilisateur').all()

    user_filter = request.GET.get('user', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if user_filter:
        logs = logs.filter(utilisateur__username__icontains=user_filter)
    if date_from:
        logs = logs.filter(cree_le__date__gte=date_from)
    if date_to:
        logs = logs.filter(cree_le__date__lte=date_to)

    # --- Pagination ---
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Recent user activity for sidebar chart
    recent_users = (
        LogActivite.objects
        .filter(cree_le__gte=now - timedelta(days=7))
        .values('utilisateur__username')
        .annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id'))
        .order_by('-count')[:10]
    )

    return render(request, 'audit/dashboard_audit.html', {
        'page_obj': page_obj,
        'count_today': count_today,
        'count_7d': count_7d,
        'count_30d': count_30d,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'recent_users': recent_users,
    })


# ---------------------------------------------------------------------------
# Access Rights Matrix
# ---------------------------------------------------------------------------

@staff_member_required
def matrix_view(request):
    """
    Renders the Direction × Application rights matrix.
    Each cell is a checkbox that triggers AJAX to toggle the habilitation.
    """
    directions = Direction.objects.prefetch_related('applications').order_by('nom')
    applications = Application.objects.filter(est_actif=True).order_by('nom')

    # Build a set of (direction_id, application_id) for quick lookup in template
    habilitations = set(
        DirectionApplication.objects.values_list('direction_id', 'application_id')
    )

    return render(request, 'audit/matrix.html', {
        'directions': directions,
        'applications': applications,
        'habilitations': habilitations,
    })


@staff_member_required
@require_POST
def toggle_habilitation(request):
    """
    AJAX POST endpoint: { direction_id, application_id }
    Toggles the DirectionApplication record (creates if absent, deletes if present).
    Returns JSON: { status: 'added'|'removed', direction_id, application_id }
    """
    try:
        data = json.loads(request.body)
        direction_id = int(data['direction_id'])
        application_id = int(data['application_id'])
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Données invalides'}, status=400)

    try:
        direction = Direction.objects.get(pk=direction_id)
        application = Application.objects.get(pk=application_id)
    except (Direction.DoesNotExist, Application.DoesNotExist):
        return JsonResponse({'error': 'Ressource introuvable'}, status=404)

    hab, created = DirectionApplication.objects.get_or_create(
        direction=direction,
        application=application,
    )

    if created:
        status = 'added'
        action = f"Habilitation ajoutée : {direction.nom} → {application.nom}"
    else:
        hab.delete()
        status = 'removed'
        action = f"Habilitation supprimée : {direction.nom} → {application.nom}"

    log_activite(request, action, {
        'direction_id': direction_id,
        'application_id': application_id,
    })

    return JsonResponse({
        'status': status,
        'direction_id': direction_id,
        'application_id': application_id,
    })
