from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CardConfig(AppConfig):
    name = 'card'
    verbose_name = _('Card mall')
