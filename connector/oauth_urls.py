"""OAuth + discovery URLs, mounted at the site root.

Kept in DOT's 'oauth2_provider' namespace because its metadata views build
endpoint URLs with reverse('oauth2_provider:...'). Only the routes the
connector needs are exposed -- no application-management pages, no implicit
or device flows.
"""

from django.urls import path
from oauth2_provider import views as dot_views
from oauth2_provider.urls import metadata_urlpatterns

from .oauth import ConnectorAuthorizationView, ConnectorRegistrationView

app_name = 'oauth2_provider'

urlpatterns = metadata_urlpatterns + [
    path('oauth/authorize/', ConnectorAuthorizationView.as_view(), name='authorize'),
    path('oauth/token/', dot_views.TokenView.as_view(), name='token'),
    path('oauth/revoke/', dot_views.RevokeTokenView.as_view(), name='revoke-token'),
    path('oauth/register/', ConnectorRegistrationView.as_view(), name='dcr-register'),
    path('oauth/register/<str:client_id>/', dot_views.DynamicClientRegistrationManagementView.as_view(),
         name='dcr-register-management'),
]
