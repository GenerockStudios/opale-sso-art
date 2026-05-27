from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # SSO (Single Sign-On)
    path('sso/authorize/', views.sso_authorize_view, name='sso_authorize'),
    path('sso/verify/', views.sso_verify_view, name='sso_verify'),

    # Directory
    path('annuaire/', views.annuaire_view, name='annuaire'),

    # Profile
    path('profil/', views.profile_view, name='profile'),
    path('profil/mot-de-passe/', views.change_password_view, name='change_password'),

    # ── Admin : Gestion des Utilisateurs ──────────────────────────────────
    path('admin/utilisateurs/', views.gestion_users_list, name='gestion_users_list'),
    path('admin/utilisateurs/creer/', views.gestion_users_create, name='gestion_users_create'),
    path('admin/utilisateurs/<int:user_id>/modifier/', views.gestion_users_edit, name='gestion_users_edit'),
    path('admin/utilisateurs/<int:user_id>/toggle/', views.gestion_users_toggle, name='gestion_users_toggle'),
    path('admin/utilisateurs/<int:user_id>/supprimer/', views.gestion_users_delete, name='gestion_users_delete'),
]
