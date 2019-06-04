from django.conf import settings
from django.urls import (
    include, path
)

from . import views

app_name = 'api'

urlpatterns = [
    path('order-payments/', views.OrderPaymentListView.as_view()),

    path('naver-order-payments/', views.NaverOrderPaymentListView.as_view()),

    path('naver-chatbot/', views.NaverChatBot.as_view())
]

if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    ]
