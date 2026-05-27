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
