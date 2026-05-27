from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Direction
from .forms import DirectionForm
from audit.logic import log_activite

staff_required = user_passes_test(lambda u: u.is_staff, login_url='/accounts/login/')

@staff_required
@login_required
def gestion_directions_list(request):
    """Liste toutes les directions avec recherche."""
    query = request.GET.get('q', '').strip()
    directions = Direction.objects.all().order_by('nom')

    if query:
        directions = directions.filter(nom__icontains=query) | directions.filter(code__icontains=query)

    return render(request, 'organizations/admin/direction_list.html', {
        'directions': directions,
        'query': query,
    })

@staff_required
@login_required
def gestion_directions_create(request):
    """Créer une nouvelle direction."""
    if request.method == 'POST':
        form = DirectionForm(request.POST)
        if form.is_valid():
            direction = form.save()
            log_activite(request, f"Création direction : {direction.nom}", {"direction_id": direction.id})
            messages.success(request, f"✅ Direction « {direction.nom} » créée avec succès.")
            return redirect('gestion_directions_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = DirectionForm()

    return render(request, 'organizations/admin/direction_form.html', {
        'form': form,
        'action': 'Créer',
        'page_title': 'Nouvelle Direction',
    })

@staff_required
@login_required
def gestion_directions_edit(request, direction_id):
    """Modifier une direction existante."""
    direction = get_object_or_404(Direction, pk=direction_id)

    if request.method == 'POST':
        form = DirectionForm(request.POST, instance=direction)
        if form.is_valid():
            direction = form.save()
            log_activite(request, f"Modification direction : {direction.nom}", {"direction_id": direction.id})
            messages.success(request, f"✅ Direction « {direction.nom} » modifiée.")
            return redirect('gestion_directions_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = DirectionForm(instance=direction)

    return render(request, 'organizations/admin/direction_form.html', {
        'form': form,
        'direction': direction,
        'action': 'Modifier',
        'page_title': f'Modifier — {direction.nom}',
    })

@staff_required
@login_required
def gestion_directions_delete(request, direction_id):
    """Supprimer définitivement une direction."""
    direction = get_object_or_404(Direction, pk=direction_id)

    if request.method == 'POST':
        nom = direction.nom
        log_activite(request, f"Suppression direction : {nom}", {"direction_id": direction.id})
        direction.delete()
        messages.success(request, f"Direction « {nom} » supprimée.")
        return redirect('gestion_directions_list')

    return render(request, 'organizations/admin/direction_confirm_delete.html', {'direction': direction})
