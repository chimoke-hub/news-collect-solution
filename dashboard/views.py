from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from collector.models import Article, Theme
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
    articles = theme.articles.all()[:100]
    return render(request, "dashboard/theme_detail.html", {"theme": theme, "articles": articles})


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
        if name and keywords:
            Theme.objects.create(
                user=request.user,
                name=name,
                keywords=keywords,
                language=language,
                frequency=frequency,
            )
            return redirect("dashboard:index")
    return render(request, "dashboard/theme_form.html", {"action": "作成"})


@login_required
def theme_edit(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    if request.method == "POST":
        theme.name = request.POST.get("name", theme.name).strip()
        theme.keywords = request.POST.get("keywords", theme.keywords).strip()
        theme.language = request.POST.get("language", theme.language)
        theme.frequency = request.POST.get("frequency", theme.frequency)
        theme.save()
        return redirect("dashboard:theme_detail", pk=theme.pk)
    return render(request, "dashboard/theme_form.html", {"theme": theme, "action": "編集"})


@login_required
@require_POST
def theme_delete(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    theme.is_active = False
    theme.save(update_fields=["is_active"])
    return redirect("dashboard:theme_list")


@login_required
@require_POST
def collect_now(request, pk):
    theme = get_object_or_404(Theme, pk=pk, user=request.user)
    # ステータスを即座に「収集中」に変更してダッシュボードにリダイレクト
    Theme.objects.filter(pk=pk).update(status=Theme.Status.COLLECTING)
    collect_for_theme.delay(theme.pk)
    return redirect("dashboard:index")
