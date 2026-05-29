from django.shortcuts import redirect, render

from collector.presets import PRESETS


def landing(request):
    """公開ランディングページ。ログイン済みならダッシュボードへ。"""
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    return render(request, "landing.html", {"presets": PRESETS})
