from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Feature apps
    path('catalogue/', include('catalogue.urls')),
    path('accounts/', include('accounts.urls')),
    path('audit/', include('audit.urls')),
    path('organizations/', include('organizations.urls')),
    path('apps/', include('poc_apps.urls')),

    # Root → landing page
    path('', TemplateView.as_view(template_name='landing.html'), name='root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
