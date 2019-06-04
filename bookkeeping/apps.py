from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BookkeepingConfig(AppConfig):
    name = 'bookkeeping'
    verbose_name = _('bookkeeping')
