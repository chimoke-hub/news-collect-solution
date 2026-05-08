from django.conf import settings
from django.db import models


class NotificationChannel(models.Model):
    """有償プラン向け通知チャンネル設定。"""

    class ChannelType(models.TextChoices):
        SLACK = "slack", "Slack"
        TEAMS = "teams", "Microsoft Teams"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="channels")
    channel_type = models.CharField(max_length=10, choices=ChannelType.choices)
    name = models.CharField(max_length=100)
    webhook_url = models.URLField(max_length=2000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.get_channel_type_display()} ({self.name})"


class ThemeChannelLink(models.Model):
    """テーマと通知チャンネルの紐付け。"""

    theme = models.ForeignKey("collector.Theme", on_delete=models.CASCADE, related_name="channel_links")
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, related_name="theme_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["theme", "channel"], name="unique_theme_channel")
        ]

    def __str__(self):
        return f"{self.theme.name} → {self.channel.name}"
