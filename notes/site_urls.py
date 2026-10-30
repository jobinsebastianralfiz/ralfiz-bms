from django.urls import include, path, re_path

from . import views

# Mounted at /notes/ in config.urls.
urlpatterns = [
    path("api/", include("notes.urls")),
    path("new/", views.new_linked_note, name="notes_new_linked"),
    path("", views.spa, name="notes_home"),
    # Every other /notes/ path is a client-side route of the React app.
    re_path(r"^(?!api/).+$", views.spa),
]
