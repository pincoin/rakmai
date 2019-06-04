import logging

from django.conf import settings
from django.core.cache import cache

from shop import settings as shop_settings
from shop.models import Store


class StoreContextMixin(object):
    logger = logging.getLogger(__name__)

    def dispatch(self, *args, **kwargs):
        code = self.kwargs.get('store') if 'store' in self.kwargs else shop_settings.DEFAULT_STORE

        cache_key = 'rabop.viewmixins.StoreContextMixin.dispatch()'.format(code)
        cache_time = settings.CACHES['default']['TIMEOUT']

        self.store = cache.get(cache_key)

        if not self.store:
            self.store = Store.objects.get(code=code)
            cache.set(cache_key, self.store, cache_time)

        self.block_size = 5
        self.chunk_size = 10

        if 'currency_code' in self.request.session:
            self.currency_code = self.request.session['currency_code']
        else:
            self.request.session['currency_code'] = 'KRW'
            self.currency_code = 'KRW'

        return super(StoreContextMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StoreContextMixin, self).get_context_data(**kwargs)

        context['store'] = self.store
        context['currency_code'] = self.currency_code
        context['currency_rate'] = shop_settings.CURRENCY_RATE

        return context
