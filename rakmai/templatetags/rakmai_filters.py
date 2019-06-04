import hashlib
from urllib.parse import urlencode

import bleach
import markdown
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
@stringfilter
def mask_ip_address(ip):
    ip_class = ip.split('.')
    ip_class[1] = 'xxx'
    return '.'.join(ip_class)


@register.filter
@stringfilter
def mask_username(username):
    return username[0] + '*' * (len(username) - 1)


@register.filter
def is_today(dt):
    return timezone.now().today().date() == timezone.localtime(dt).date()


@register.filter
@stringfilter
def markdownify(text):
    return mark_safe(
        bleach.clean(
            markdown.markdown(text, output_format='html5', extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
            ]),
            tags=settings.BLEACH_ALLOWED_TAGS, attributes=settings.BLEACH_ALLOWED_ATTRIBUTES, strip=True,
        )
    )


@register.filter
@stringfilter
def clean_html(text):
    return mark_safe(
        bleach.clean(
            text,
            tags=settings.BLEACH_ALLOWED_TAGS, attributes=settings.BLEACH_ALLOWED_ATTRIBUTES, strip=True,
        )
    )


@register.filter
@stringfilter
def strip_html(text):
    return bleach.clean(
        text,
        tags=[], attributes={}, strip=True,
    )


@register.filter
def gravatar_url(email, size=40, default="identicon"):
    email_hash = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    query_string = urlencode({'s': str(size), 'default': default})

    return 'https://www.gravatar.com/avatar/{}?{}'.format(email_hash, query_string)
