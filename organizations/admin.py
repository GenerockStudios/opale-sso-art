from django.contrib import admin
from .models import Direction

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'created_at')
    search_fields = ('nom', 'code')
