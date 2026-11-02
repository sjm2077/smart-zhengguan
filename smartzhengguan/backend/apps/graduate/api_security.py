from time import time

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import ParseError, Throttled


RATE_LIMIT_SETTING_MAP = {
    "public_read": "PUBLIC_API_RATE_LIMIT_READ",
    "public_search": "PUBLIC_API_RATE_LIMIT_SEARCH",
    "public_query": "PUBLIC_API_RATE_LIMIT_QUERY",
    "public_meta": "PUBLIC_API_RATE_LIMIT_META",
    "prediction_data": "PREDICTION_RATE_LIMIT_DATA",
    "prediction_context": "PREDICTION_RATE_LIMIT_CONTEXT",
    "prediction_analyze": "PREDICTION_RATE_LIMIT_ANALYZE",
    "prediction_chat": "PREDICTION_RATE_LIMIT_CHAT",
}


def client_ip_from_request(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    return request.META.get("REMOTE_ADDR", "unknown").strip() or "unknown"


def get_prediction_rate_limit(scope):
    setting_name = RATE_LIMIT_SETTING_MAP.get(scope, "")
    if not setting_name:
        return 0
    return max(0, int(getattr(settings, setting_name, 0) or 0))


def prediction_rate_limit_window_seconds():
    return max(1, int(getattr(settings, "PREDICTION_RATE_LIMIT_WINDOW_SECONDS", 60) or 60))


def enforce_prediction_request_size(request):
    if request.method.upper() not in {"POST", "PUT", "PATCH"}:
        return
    raw_length = request.META.get("CONTENT_LENGTH", "")
    if raw_length in ("", None):
        return
    try:
        content_length = int(raw_length)
    except (TypeError, ValueError):
        return
    max_bytes = int(getattr(settings, "PREDICTION_MAX_REQUEST_BYTES", 16384) or 16384)
    if content_length > max_bytes:
        raise ParseError(f"request body exceeds {max_bytes} bytes")


def enforce_prediction_rate_limit(request, scope):
    limit = get_prediction_rate_limit(scope)
    if limit <= 0:
        return

    window = prediction_rate_limit_window_seconds()
    ip = client_ip_from_request(request)
    bucket = int(time())
    slot = bucket // window
    cache_key = f"prediction-rate:{scope}:{ip}:{slot}"

    if cache.add(cache_key, 1, timeout=window):
        return

    try:
        current = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=window)
        current = 1

    if current > limit:
        wait_seconds = max(1, window - (bucket % window))
        raise Throttled(detail="request rate exceeded", wait=wait_seconds)


class PredictionApiSecurityMixin:
    security_scope = ""

    def initial(self, request, *args, **kwargs):
        enforce_prediction_request_size(request)
        if self.security_scope:
            enforce_prediction_rate_limit(request, self.security_scope)
        return super().initial(request, *args, **kwargs)
