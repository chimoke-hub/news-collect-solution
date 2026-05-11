from django.conf import settings
from django.db import models


class Theme(models.Model):
    """ユーザーが設定するニュース収集テーマ。"""

    class Language(models.TextChoices):
        JA = "ja", "日本語"
        EN = "en", "英語"
        BOTH = "both", "両方"

    class Frequency(models.TextChoices):
        DAILY = "daily", "毎日"
        WEEKLY = "weekly", "毎週"

    class Status(models.TextChoices):
        IDLE = "idle", "待機中"
        COLLECTING = "collecting", "収集中"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="themes")
    name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="収集キーワード（スペース区切りまたはOR/AND）")
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.BOTH)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.DAILY)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.IDLE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_collected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.name}"


class Article(models.Model):
    """収集された記事。"""

    class Category(models.TextChoices):
        DOMESTIC = "domestic", "国内"
        INTERNATIONAL = "international", "海外"

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="articles")
    title = models.CharField(max_length=500)
    title_ja = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=2000)
    source = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    published_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        constraints = [
            models.UniqueConstraint(fields=["theme", "url"], name="unique_article_per_theme")
        ]

    def __str__(self):
        return self.title

    @property
    def display_title(self):
        return self.title_ja or self.title
