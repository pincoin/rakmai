from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BannerConfig(AppConfig):
    name = 'banner'
    verbose_name = _('banner')
