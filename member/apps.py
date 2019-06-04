from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MemberConfig(AppConfig):
    name = 'member'
    verbose_name = _('member')

    def ready(self):
        import member.signals