"""Celeryタスク: ユーザーテーマごとのニュース収集。"""

import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from django.utils import timezone as django_tz

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_for_theme(self, theme_id: int):
    from collector.engine import collect_newsapi, collect_rss_from_urls, translate_titles
    from collector.models import Article, Theme

    try:
        theme = Theme.objects.get(pk=theme_id, is_active=True)
    except Theme.DoesNotExist:
        logger.warning("Theme %d not found or inactive", theme_id)
        return

    # 収集開始：ステータスを更新
    Theme.objects.filter(pk=theme_id).update(status=Theme.Status.COLLECTING)

    try:
        # 初回は7日分、以降はlast_collected_atから（重複はDB制約で排除）
        if theme.last_collected_at:
            since = theme.last_collected_at - timedelta(hours=1)
        else:
            since = datetime.now(timezone.utc) - timedelta(days=7)

        newsapi_articles = collect_newsapi(theme.keywords, since, theme.language)
        rss_articles = collect_rss_from_urls(theme.rss_feed_urls, theme.keywords, since)
        all_articles = newsapi_articles + rss_articles

        international = [a for a in all_articles if a.get("category") == "international"]
        if international:
            translate_titles(international)

        saved = 0
        for data in all_articles:
            _, created = Article.objects.get_or_create(
                theme=theme,
                url=data["url"],
                defaults={
                    "title": data["title"],
                    "title_ja": data.get("title_ja", ""),
                    "source": data["source"],
                    "category": data["category"],
                    "published_at": data["published_at"],
                },
            )
            if created:
                saved += 1

        logger.info("Theme %d (%s): saved %d new articles", theme_id, theme.name, saved)

        if theme.user.is_paid:
            send_notifications_for_theme.delay(theme_id)

        return saved

    finally:
        # 収集完了：ステータスをリセット（エラー時も必ず実行）
        Theme.objects.filter(pk=theme_id).update(
            status=Theme.Status.IDLE,
            last_collected_at=django_tz.now(),
        )


@shared_task
def collect_all_active_themes():
    """全アクティブテーマの収集を起動。GitHub Actionsまたはcelery-beatから呼び出す。"""
    from collector.models import Theme

    theme_ids = list(Theme.objects.filter(is_active=True).values_list("id", flat=True))
    for theme_id in theme_ids:
        collect_for_theme.delay(theme_id)

    logger.info("Queued collection for %d themes", len(theme_ids))
    return len(theme_ids)


@shared_task
def send_notifications_for_theme(theme_id: int):
    from collector.models import Article, Theme
    from notifications.sender import send_to_channel

    try:
        theme = Theme.objects.get(pk=theme_id)
    except Theme.DoesNotExist:
        return

    articles = Article.objects.filter(
        theme=theme,
        collected_at__gte=theme.last_collected_at,
    ).order_by("-published_at")[:50]

    if not articles:
        return

    for link in theme.channel_links.select_related("channel").filter(channel__is_active=True):
        send_to_channel(link.channel, theme, list(articles))
