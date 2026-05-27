from django.urls import path
from . import views

urlpatterns = [
    path('admin/directions/', views.gestion_directions_list, name='gestion_directions_list'),
    path('admin/directions/creer/', views.gestion_directions_create, name='gestion_directions_create'),
    path('admin/directions/<int:direction_id>/modifier/', views.gestion_directions_edit, name='gestion_directions_edit'),
    path('admin/directions/<int:direction_id>/supprimer/', views.gestion_directions_delete, name='gestion_directions_delete'),
]
