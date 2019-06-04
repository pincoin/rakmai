from django.urls import (
    path, re_path
)

from . import views

app_name = 'card'

urlpatterns = [
    path('<str:store>/',
         views.HomeView.as_view(), name='home'),

    re_path(r'^(?P<store>[-\w]+)/category/(?P<slug>[-\w]+)/$',
            views.ProductCategoryView.as_view(), name='product-category'),

    path('<str:store>/products/',
         views.ProductListView.as_view(), name='product-list'),

    path('<str:store>/<int:pk>/<str:code>/',
         views.ProductDetailView.as_view(), name='product-detail'),

    path('<str:store>/cart/',
         views.CartView.as_view(), name='cart'),

    path('<str:store>/cart/add/',
         views.CartAddView.as_view(), name='cart-add'),

    path('<str:store>/cart/remove/',
         views.CartRemoveView.as_view(), name='cart-remove'),

    path('<str:store>/cart/delete/',
         views.CartDeleteView.as_view(), name='cart-delete'),

    path('<str:store>/cart/clear/',
         views.CartClearView.as_view(), name='cart-clear'),

    path('<str:store>/cart/set-quantity/',
         views.CartSetQuantityView.as_view(), name='cart-set-quantity'),

    path('<str:store>/orders/',
         views.OrderListView.as_view(), name='order-list'),

    path('<str:store>/orders/<uuid:uuid>/',
         views.OrderDetailView.as_view(), name='order-detail'),

    path('<str:store>/orders/<uuid:uuid>/receipt',
         views.OrderReceiptView.as_view(), name='order-receipt'),

    path('<str:store>/orders/<uuid:uuid>/again',
         views.OrderAgainView.as_view(), name='order-again'),

    path('<str:store>/orders/<uuid:uuid>/delete/',
         views.OrderDeleteView.as_view(), name='order-delete'),

    path('<str:store>/orders/<uuid:uuid>/hide/',
         views.OrderHideView.as_view(), name='order-hide'),

    path('<str:store>/orders/<uuid:uuid>/refund/',
         views.OrderRefundCreateView.as_view(), name='refund-create'),

    path('<str:store>/currency/',
         views.CurrencyUpdateView.as_view(), name='currency-update'),

    path('<str:store>/payment/iamport/callback/',
         views.IamportCallbackView.as_view(), name='iamport-callback'),
]
