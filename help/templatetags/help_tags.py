from django import template
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from shop.models import (
    NoticeMessage, Testimonials, CustomerQuestion, Order
)

register = template.Library()


@register.simple_tag
def get_notice(store_code='default', mall='www', count=5):
    cache_key = 'help.templatetags.help_tags.get_notice({}-{})'.format(store_code, mall)
    cache_time = settings.CACHES['default']['TIMEOUT']
    notices = cache.get(cache_key)

    if not notices:
        if mall == 'card':
            notices = NoticeMessage.objects \
                          .filter(store__code=store_code) \
                          .exclude(category=NoticeMessage.CATEGORY_CHOICES.price) \
                          .order_by('-created')[:count]
        else:
            notices = NoticeMessage.objects \
                          .filter(store__code=store_code) \
                          .order_by('-created')[:count]

        cache.set(cache_key, notices, cache_time)

    return notices


@register.simple_tag
def get_testimonials(store_code='default', count=5):
    cache_key = 'help.templatetags.help_tags.get_testimonials({})'.format(store_code)
    cache_time = settings.CACHES['default']['TIMEOUT']
    testimonials = cache.get(cache_key)

    if not testimonials:
        testimonials = Testimonials.objects.filter(store__code=store_code).order_by('-created')[:count]
        cache.set(cache_key, testimonials, cache_time)

    return testimonials


@register.simple_tag(takes_context=True)
def get_customer_questions(context, store_code, count):
    questions = CustomerQuestion.objects \
                    .filter(store__code=store_code, is_removed=False, owner=context['request'].user) \
                    .annotate(answers_count=Count('answers')) \
                    .order_by('-created')[:count]

    return questions



@register.simple_tag
def get_recent_orders(user_id, count):
    return Order.objects \
               .select_related('user', 'user__profile') \
               .filter(is_removed=False, user__id=user_id)[:count]
