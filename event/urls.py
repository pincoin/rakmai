from django.urls import (
    path
)

from . import views

app_name = 'event'

urlpatterns = [
    path('lotte-card/pc/',
         views.LotteCardPCView.as_view(), name='lotte-card-pc'),
    path('lotte-card/mobile/',
         views.LotteCardMobileView.as_view(), name='lotte-card-mobile'),
]
