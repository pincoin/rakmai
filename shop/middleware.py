import logging

from django.conf import settings
from ipware.ip import get_ip

from .models import NaverAdvertisementLog


class AdvertisementLogMiddleware:
    logger = logging.getLogger(__name__)

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        if request.method == 'GET' \
                and not request.path.startswith(settings.STATIC_URL) \
                and not request.path.startswith(settings.MEDIA_URL):

            # Naver
            if all(k in request.GET for k in (
                    'n_campaign_type',
                    'n_media',
                    'n_query',
                    'n_rank',
                    'n_ad_group',
                    'n_ad',
                    'n_keyword_id',
                    'n_keyword')):
                log = NaverAdvertisementLog()

                log.ip_address = get_ip(request)
                log.user_agent = request.META['HTTP_USER_AGENT']

                log.campaign_type = request.GET['n_campaign_type'] if request.GET['n_campaign_type'].isdigit() else 1
                log.media = request.GET['n_media']
                log.query = request.GET['n_query']
                log.rank = request.GET['n_rank']
                log.ad_group = request.GET['n_ad_group']
                log.ad = request.GET['n_ad']
                log.keyword_id = request.GET['n_keyword_id']
                log.keyword = request.GET['n_keyword']

                log.save()

            # Google

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
