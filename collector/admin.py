from django.contrib import admin
from .models import Article, Theme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "language", "frequency", "is_active", "last_collected_at")
    list_filter = ("language", "frequency", "is_active")
    search_fields = ("name", "user__email", "keywords")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("display_title", "source", "category", "published_at", "theme")
    list_filter = ("category", "source")
    search_fields = ("title", "title_ja", "url")
    date_hierarchy = "published_at"
