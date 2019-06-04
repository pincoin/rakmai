from ipware.ip import get_ip
from rest_framework import permissions

from . import settings as api_settings


class WhiteListPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        ip_addr = get_ip(request)

        return True if ip_addr in api_settings.REST_FRAMEWORK_WHITELIST else False
