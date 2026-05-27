from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.audit_dashboard, name='audit_logs'),
    path('matrice/', views.matrix_view, name='audit_matrix'),
    path('toggle-habilitation/', views.toggle_habilitation, name='toggle_habilitation'),
]
