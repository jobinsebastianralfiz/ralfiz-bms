from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from employees.views import CertificateVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/license/', include('licensing.urls')),
    path('api/gympro/', include('gympro_licensing.urls')),
    path('api/eduflow/', include('eduflow_licensing.urls')),
    path('api/retailease/', include('retailease.urls')),
    path('api/interiodesk/', include('interiodesk.urls')),
    path('crm/', include('crm.urls')),
    path('api/employees/', include('employees.urls')),
    path('api/client/', include('client_portal.api_urls')),
    path('api/pulse/', include('pulse.urls')),
    path('portal/', include('client_portal.urls')),
    path('staff/', include('employees.portal_urls')),
    path('agreement/', include('employees.agreement_urls')),

    # Short verification link. It is what the certificate QR encodes: the API
    # path is 96 characters, which pushes the code to 49 modules and leaves
    # each one under half a millimetre on the printed page. The long path
    # stays so codes already in the wild keep working.
    path('v/<uuid:verification_id>/', CertificateVerifyView.as_view(), name='certificate_verify_short'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('', include('core.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Always serve media files (needed for uploaded logos, etc.)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
