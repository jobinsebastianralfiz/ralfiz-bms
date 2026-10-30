from django.urls import path
from rest_framework.routers import SimpleRouter

from doc_templates.api import TemplateViewSet

from . import api

router = SimpleRouter()
router.register("notes", api.NoteViewSet, basename="note")
router.register("folders", api.FolderViewSet, basename="folder")
router.register("templates", TemplateViewSet, basename="template")

# The JSON API the Notes app calls, mounted at /notes/api/ (see notes.site_urls).
urlpatterns = [
    path("auth/me/", api.MeView.as_view()),
    path("auth/csrf/", api.CsrfView.as_view()),
    path("assets/", api.AssetUploadView.as_view()),
    path("assets/<uuid:pk>/", api.AssetFileView.as_view()),
    *router.urls,
]
