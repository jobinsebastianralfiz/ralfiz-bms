from django.conf import settings
from django.db import models


class ConnectorCallLog(models.Model):
    """One row per tool call made through the Claude connector.

    Written for every tools/call, successful or not, so there is a plain record
    of what Claude read or changed on whose behalf.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='connector_calls',
    )
    client_name = models.CharField(max_length=255, blank=True)
    tool = models.CharField(max_length=100)
    arguments = models.JSONField(default=dict, blank=True)
    is_write = models.BooleanField(default=False)
    ok = models.BooleanField(default=True)
    error = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tool} by {self.user} at {self.created_at:%Y-%m-%d %H:%M}'
