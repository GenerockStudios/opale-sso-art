from django.urls import path
from .views import DashboardView, launch_app
from . import views

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('launch/<int:app_id>/', launch_app, name='launch_app'),

    # ── Admin : Gestion des Applications ──────────────────────────────────
    path('admin/applications/', views.gestion_apps_list, name='gestion_apps_list'),
    path('admin/applications/creer/', views.gestion_apps_create, name='gestion_apps_create'),
    path('admin/applications/<int:app_id>/modifier/', views.gestion_apps_edit, name='gestion_apps_edit'),
    path('admin/applications/<int:app_id>/toggle/', views.gestion_apps_toggle, name='gestion_apps_toggle'),
    path('admin/applications/<int:app_id>/supprimer/', views.gestion_apps_delete, name='gestion_apps_delete'),
]
