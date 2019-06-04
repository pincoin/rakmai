from django import template

from ..models import Message

register = template.Library()


@register.simple_tag
def get_recent_messages(count=10):
    messages = Message.objects \
                   .select_related('board') \
                   .published() \
                   .public(). \
                   order_by('-created')[:count]
    return messages
