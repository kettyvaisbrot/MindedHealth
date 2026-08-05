from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """DB + Redis liveness check for the Docker Compose healthcheck.

    No auth -- infra probes hit this anonymously. Checks real connectivity,
    not just "the process is up", since that's the gap this endpoint exists
    to close.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:
        return JsonResponse({"status": "error", "component": "database", "detail": str(exc)}, status=503)

    try:
        cache.set("healthz", "1", timeout=5)
        if cache.get("healthz") != "1":
            raise RuntimeError("cache round-trip mismatch")
    except Exception as exc:
        return JsonResponse({"status": "error", "component": "redis", "detail": str(exc)}, status=503)

    return JsonResponse({"status": "ok"})
