from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime

from collector.models import Article, Theme
from collector.presets import PRESETS
from collector.tasks import collect_for_theme


@login_required
def index(request):
    themes = request.user.themes.prefetch_related("articles").filter(is_active=True)
    return render(request, "dashboard/index.html", {"themes": themes})


@login_required
def theme_list(request):
    themes = request.user.themes.all()
    return render(request, "dashboard/theme_list.html", {"themes": themes})


@login_required
def theme_detail(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    articles_qs = theme.articles.order_by("-collected_at", "-published_at")[:200]

    # 収集日でグループ化
    grouped = {}
    for article in articles_qs:
        day = localtime(article.collected_at).date()
        grouped.setdefault(day, []).append(article)

    return render(request, "dashboard/theme_detail.html", {
        "theme": theme,
        "grouped_articles": sorted(grouped.items(), reverse=True),
        "total": articles_qs.count(),
    })


@login_required
def theme_create(request):
    free_limit = 1
    if not request.user.is_paid and request.user.themes.filter(is_active=True).count() >= free_limit:
        return render(request, "dashboard/plan_required.html", {"reason": "theme_limit"})

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        keywords = request.POST.get("keywords", "").strip()
        language = request.POST.get("language", "both")
        frequency = request.POST.get("frequency", "daily")
        rss_feeds = request.POST.get("rss_feeds", "").strip()
        if name and keywords:
            Theme.objects.create(
                user=request.user,
                name=name,
                keywords=keywords,
                language=language,
                frequency=frequency,
                rss_feeds=rss_feeds,
            )
            return redirect("dashboard:index")
    return render(request, "dashboard/theme_form.html", {
        "action": "作成",
        "presets": PRESETS,
        "welcome": request.GET.get("welcome") == "1",
    })


@login_required
def theme_edit(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    if request.method == "POST":
        theme.name = request.POST.get("name", theme.name).strip()
        theme.keywords = request.POST.get("keywords", theme.keywords).strip()
        theme.language = request.POST.get("language", theme.language)
        theme.frequency = request.POST.get("frequency", theme.frequency)
        theme.rss_feeds = request.POST.get("rss_feeds", theme.rss_feeds).strip()
        theme.save()
        return redirect("dashboard:theme_detail", pk=theme.pk)
    return render(request, "dashboard/theme_form.html", {
        "theme": theme,
        "action": "編集",
        "presets": PRESETS,
    })


@login_required
@require_POST
def theme_delete(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    theme.is_active = False
    theme.save(update_fields=["is_active"])
    return redirect("dashboard:theme_list")


@login_required
@require_POST
def theme_reset(request, pk):
    """テーマの収集記事をすべて削除してリセット。"""
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    count, _ = theme.articles.all().delete()
    Theme.objects.filter(pk=pk).update(last_collected_at=None)
    return redirect("dashboard:theme_detail", pk=theme.pk)


@login_required
@require_POST
def collect_now(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    Theme.objects.filter(pk=pk).update(status=Theme.Status.COLLECTING)
    collect_for_theme.delay(theme.pk)
    return redirect("dashboard:index")


@login_required
@require_POST
def article_delete(request, pk):
    """記事を個別削除。"""
    article = get_object_or_404(Article, pk=pk, theme__user=request.user)
    theme_pk = article.theme_id
    article.delete()
    return redirect("dashboard:theme_detail", pk=theme_pk)


@login_required
@require_POST
def article_favorite_toggle(request, pk):
    """記事のお気に入りをトグル。"""
    article = get_object_or_404(Article, pk=pk, theme__user=request.user)
    article.is_favorite = not article.is_favorite
    article.save(update_fields=["is_favorite"])
    next_url = request.POST.get("next", "")
    if next_url == "favorites":
        return redirect("dashboard:favorites")
    return redirect("dashboard:theme_detail", pk=article.theme_id)


@login_required
def favorites(request):
    """お気に入り記事一覧。"""
    articles = Article.objects.filter(
        theme__user=request.user,
        is_favorite=True,
    ).select_related("theme").order_by("-published_at")
    return render(request, "dashboard/favorites.html", {"articles": articles})
