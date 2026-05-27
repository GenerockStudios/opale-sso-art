"""
audit/logic.py
Centralized audit logging for the OPALE Service Hub.
All app access and user actions must pass through log_activite().
"""
from .models import LogActivite


def get_client_ip(request):
    """Extracts real IP from proxy headers or REMOTE_ADDR."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (client IP)
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def log_activite(request, action, details=None):
    """
    Creates a LogActivite record for the current request.

    Args:
        request: The Django HttpRequest object.
        action (str): A human-readable description of the action (e.g. "Accès Logiciel : SIGFIP").
        details (dict|None): Optional JSON-compatible dict with extra context.

    Returns:
        LogActivite: The created log instance.
    """
    user = request.user if request.user.is_authenticated else None
    ip = get_client_ip(request)

    return LogActivite.objects.create(
        utilisateur=user,
        action=action,
        ip_address=ip,
        details=details or {},
    )
