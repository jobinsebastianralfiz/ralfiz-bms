from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]  # Next.js dev server
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# Plain static storage in dev/tests so collectstatic isn't required
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405
