from django.contrib import admin
from .models import LogActivite

@admin.register(LogActivite)
class LogActiviteAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'cree_le')
    list_filter = ('utilisateur', 'action', 'cree_le')
    search_fields = ('action', 'utilisateur__username', 'details')
    readonly_fields = ('utilisateur', 'action', 'details', 'cree_le')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
