import hmac
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .tasks import collect_all_active_themes


@csrf_exempt
@require_POST
def trigger_collect(request):
    """GitHub ActionsからCeleryタスクを起動するエンドポイント。"""
    auth = request.headers.get("Authorization", "")
    secret = getattr(settings, "COLLECT_SECRET", "")

    if not secret or not hmac.compare_digest(auth, f"Bearer {secret}"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    result = collect_all_active_themes.delay()
    return JsonResponse({"status": "queued", "task_id": str(result.id)})
