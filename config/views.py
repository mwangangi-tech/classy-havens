import logging
from django.shortcuts import render

logger = logging.getLogger("security")


def csrf_failure(request, reason=""):
    logger.warning(
        "csrf_failure path=%s reason=%s user=%s ip=%s",
        request.path,
        reason,
        getattr(request.user, "username", "anonymous"),
        request.META.get("REMOTE_ADDR"),
    )
    return render(request, "csrf_failure.html", {"reason": reason}, status=403)