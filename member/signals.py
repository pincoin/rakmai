from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from ipware import get_client_ip

from .models import LoginLog


@receiver(user_logged_in)
def login_logger(request, user, **kwargs):
    login_log = LoginLog()
    login_log.user = user
    login_log.ip_address = get_client_ip(request)[0]
    login_log.save()
