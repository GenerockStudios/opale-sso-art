from django.contrib import admin
from .models import Application, DirectionApplication

class DirectionApplicationInline(admin.TabularInline):
    model = DirectionApplication
    extra = 1

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'url_acces', 'icone_name', 'est_actif')
    list_filter = ('est_actif', 'directions_autorisees')
    search_fields = ('nom', 'description')
    inlines = [DirectionApplicationInline]

@admin.register(DirectionApplication)
class DirectionApplicationAdmin(admin.ModelAdmin):
    list_display = ('direction', 'application', 'date_attribution')
    list_filter = ('direction', 'application')
