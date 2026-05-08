from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import NotificationChannel, ThemeChannelLink
from collector.models import Theme


@login_required
def channel_list(request):
    if not request.user.is_paid:
        return render(request, "dashboard/plan_required.html", {"reason": "notifications"})
    channels = request.user.channels.all()
    return render(request, "notifications/channel_list.html", {"channels": channels})


@login_required
def channel_create(request):
    if not request.user.is_paid:
        return render(request, "dashboard/plan_required.html", {"reason": "notifications"})
    if request.method == "POST":
        channel_type = request.POST.get("channel_type")
        name = request.POST.get("name", "").strip()
        webhook_url = request.POST.get("webhook_url", "").strip()
        if channel_type and name and webhook_url:
            NotificationChannel.objects.create(
                user=request.user,
                channel_type=channel_type,
                name=name,
                webhook_url=webhook_url,
            )
            return redirect("notifications:channel_list")
    return render(request, "notifications/channel_form.html", {
        "channel_types": NotificationChannel.ChannelType.choices,
    })


@login_required
@require_POST
def channel_delete(request, pk):
    channel = get_object_or_404(NotificationChannel, pk=pk, user=request.user)
    channel.delete()
    return redirect("notifications:channel_list")


@login_required
def channel_link(request, theme_pk):
    if not request.user.is_paid:
        return render(request, "dashboard/plan_required.html", {"reason": "notifications"})
    theme = get_object_or_404(Theme, pk=theme_pk, user=request.user)
    channels = request.user.channels.filter(is_active=True)
    linked_ids = set(theme.channel_links.values_list("channel_id", flat=True))

    if request.method == "POST":
        selected_ids = set(map(int, request.POST.getlist("channel_ids")))
        to_add = selected_ids - linked_ids
        to_remove = linked_ids - selected_ids
        for ch_id in to_add:
            ThemeChannelLink.objects.get_or_create(theme=theme, channel_id=ch_id)
        ThemeChannelLink.objects.filter(theme=theme, channel_id__in=to_remove).delete()
        return redirect("dashboard:theme_detail", pk=theme.pk)

    return render(request, "notifications/channel_link.html", {
        "theme": theme,
        "channels": channels,
        "linked_ids": linked_ids,
    })
