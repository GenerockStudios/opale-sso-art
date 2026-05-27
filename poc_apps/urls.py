from django.urls import path
from . import views

urlpatterns = [
    path('zimbra-mail/', views.zimbra_mail_view, name='zimbra_mail'),
    path('licences/', views.telecom_licences_view, name='telecom_licences'),
    path('spectre/', views.spectre_monitoring_view, name='spectre_monitoring'),
    path('sso-callback/', views.sso_callback_view, name='sso_callback'),
    path('logout/', views.poc_logout_view, name='poc_logout'),
]
