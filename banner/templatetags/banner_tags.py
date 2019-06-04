from django import template
from django.utils.timezone import now

from ..models import Banner

register = template.Library()


@register.simple_tag
def get_banner(title=''):
    try:
        banner = Banner.objects.get(title=title, status=Banner.STATUS_CHOICES.enabled)
    except Banner.DoesNotExist:
        return None

    if banner.start and banner.start > now():
        return None

    if banner.end and banner.end < now():
        return None

    return banner.banners.all()
