from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'direction', 'is_staff')
    list_filter = ('role', 'direction', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations ART', {'fields': ('role', 'direction')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations ART', {'fields': ('role', 'direction')}),
    )

    def save_model(self, request, obj, form, change):
        # Enregistrer en base locale d'abord
        super().save_model(request, obj, form, change)
        
        # Synchroniser avec AD/LDAP
        from accounts.ad_client import get_ad_client
        client = get_ad_client()
        if client.is_enabled():
            try:
                if not change:
                    raw_pwd = form.cleaned_data.get('password') or "Password123!"
                    client.create_user(obj, password=raw_pwd)
                else:
                    raw_pwd = form.cleaned_data.get('password') if 'password' in form.cleaned_data else None
                    client.update_user(obj, password=raw_pwd)
                    
                    if 'is_active' in form.changed_data:
                        client.toggle_user_status(obj.username, obj.is_active)
            except Exception as ad_err:
                from django.contrib import messages
                messages.warning(request, f"⚠️ Utilisateur enregistré en base locale, mais la synchronisation Active Directory a échoué : {ad_err}")

    def delete_model(self, request, obj):
        username = obj.username
        
        # Synchroniser avec AD/LDAP
        from accounts.ad_client import get_ad_client
        client = get_ad_client()
        ad_sync_success = True
        ad_err_msg = ""
        if client.is_enabled():
            try:
                client.delete_user(username)
            except Exception as ad_err:
                ad_sync_success = False
                ad_err_msg = str(ad_err)
                
        # Supprimer en base locale
        super().delete_model(request, obj)
        
        if not ad_sync_success:
            from django.contrib import messages
            messages.warning(request, f"⚠️ Utilisateur supprimé localement, mais la suppression de l'annuaire Active Directory a échoué : {ad_err_msg}")

