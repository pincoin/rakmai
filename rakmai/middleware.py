import logging
from importlib import import_module

from django.conf import settings
from django.contrib.gis.geoip2 import GeoIP2
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from geoip2.errors import AddressNotFoundError
from ipware.ip import get_ip


class UserRestrict(MiddlewareMixin):
    logger = logging.getLogger(__name__)

    def process_request(self, request):
        if request.user.is_authenticated:
            cache_key = 'rakmai.middleware.UserRestrict.process_request({})'.format(request.user.pk)
            cache_time = 3600

            session_key = cache.get(cache_key)

            if session_key:
                if request.session.session_key != session_key:
                    self.logger.info('duplicate login: user.pk-{} session_key-{} session_key(cached)-{}'
                                     .format(request.user.pk, request.session.session_key, session_key))
                    engine = import_module(settings.SESSION_ENGINE)
                    session = engine.SessionStore(session_key=session_key)
                    session.delete()
                    cache.set(cache_key, request.session.session_key, cache_time)
            else:
                cache.set(cache_key, request.session.session_key, cache_time)


class GeoIPRestrict(MiddlewareMixin):
    logger = logging.getLogger(__name__)

    def process_request(self, request):
        try:
            ip_address = get_ip(request)
            if ip_address not in ['127.0.0.1']:
                country = GeoIP2().country(ip_address)

                if country['country_code'] and country['country_code'].upper() in settings.BLOCK_COUNTRY_CODES:
                    return HttpResponseForbidden("")
        except AddressNotFoundError:
            pass
