from django.db import models


class TimeStampedModel(models.Model):
    """Every business table gets created_at / updated_at for free."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
