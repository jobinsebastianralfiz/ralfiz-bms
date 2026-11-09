import logging
import time

logger = logging.getLogger("bookit.performance")
SLOW_MS = 500


class SlowRequestLogMiddleware:
    """Logs any request slower than SLOW_MS and adds a timing header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > SLOW_MS:
            logger.warning("SLOW %s %s took %.0f ms", request.method, request.path, elapsed_ms)
        response["X-Response-Time-ms"] = f"{elapsed_ms:.0f}"
        return response
