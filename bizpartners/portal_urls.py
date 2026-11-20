from django.urls import path

from . import issue_views as iv
from . import portal_views as v

app_name = 'bizpartners_portal'

urlpatterns = [
    path('login/', v.portal_login, name='login'),
    path('logout/', v.portal_logout, name='logout'),
    path('', v.dashboard, name='dashboard'),
    path('projects/', v.projects, name='projects'),
    path('projects/<uuid:pk>/', v.project_detail, name='project'),
    path('projects/<uuid:pk>/issues/export/', iv.portal_issue_export, name='issue_export'),
    path('projects/<uuid:pk>/issues/read/', iv.portal_issue_draft, name='issue_draft'),
    path('projects/<uuid:pk>/issues/add/', iv.portal_issue_add, name='issue_add'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/file/', v.item_file, name='item_file'),
    path('payments/', v.payments, name='payments'),
    path('quotes/', v.quotes, name='quotes'),
    path('password/', v.change_password, name='password'),
]
