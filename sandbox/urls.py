from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import (
    include, path
)
from django.views.generic import TemplateView

from rakmai.views import HomeView

urlpatterns = [
    path('',
         HomeView.as_view(), name='home'),

    path('accounts/',
         include('member.urls')),

    path('i18n/',
         include('django.conf.urls.i18n')),

    path('{}'.format(settings.ADMIN_URL),
         admin.site.urls),

    path('robots.txt', TemplateView.as_view(template_name='rakmai/robots.txt', content_type='text/plain')),
]

if 'blog' in settings.INSTALLED_APPS:
    urlpatterns += path('blog/', include('blog.urls', namespace='blog')),

if 'board' in settings.INSTALLED_APPS:
    urlpatterns += path('board/', include('board.urls', namespace='board')),

if 'book' in settings.INSTALLED_APPS:
    urlpatterns += path('book/', include('book.urls', namespace='book')),

if 'shop' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('shop/',
             include('shop.urls', namespace='shop')),
        path('help/',
             include('help.urls', namespace='help')),
        path('{}'.format(settings.RABOP_URL),
             include('rabop.urls', namespace='rabop')),
        path('{}'.format(settings.API_URL),
             include('api.urls', namespace='api')),
    ]

if 'card' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('card/',
             include('card.urls', namespace='card')),
    ]

if 'event' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('event/',
             include('event.urls', namespace='event')),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

if settings.GOOGLE_OTP_ENABLED:
    from django_otp.admin import OTPAdminSite

    admin.site.__class__ = OTPAdminSite
