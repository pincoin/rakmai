from django.contrib.sitemaps.views import sitemap
from django.urls import (
    path, re_path
)

from blog.sitemaps import PostSitemap as BlogPostSitemap
from book.sitemaps import PageSitemap as BookPageSitemap
from . import views
from .sitemaps import (
    StaticSitemap, ProductCategorySitemap, ProductSitemap, NoticeMessageSitemap, TestimonialsSitemap
)

app_name = 'shop'

sitemaps_static = {
    'sitemap': StaticSitemap(),
}

sitemaps_product_category = {
    'sitemap': ProductCategorySitemap(),
}

sitemaps_product = {
    'sitemap': ProductSitemap(),
}

sitemaps_notice_message = {
    'sitemap': NoticeMessageSitemap(),
}

sitemaps_testimonials = {
    'sitemap': TestimonialsSitemap(),
}

sitemaps_blog_posts = {
    'sitemap': BlogPostSitemap(),
}

sitemaps_book_pages = {
    'sitemap': BookPageSitemap(),
}

sitemaps_all = {}
sitemaps_all.update(sitemaps_static)
sitemaps_all.update(sitemaps_product_category)
sitemaps_all.update(sitemaps_product)
sitemaps_all.update(sitemaps_notice_message)
sitemaps_all.update(sitemaps_testimonials)
sitemaps_all.update(sitemaps_blog_posts)
sitemaps_all.update(sitemaps_book_pages)

urlpatterns = [
    path('<str:store>/',
         views.HomeView.as_view(), name='home'),

    path('<str:store>/products/',
         views.ProductListView.as_view(), name='product-list'),

    path('<str:store>/<int:pk>/<str:code>/',
         views.ProductDetailView.as_view(), name='product-detail'),

    path('<str:store>/<int:pk>/<str:code>/card/',
         views.ProductDetailRedirectView.as_view(), name='product-detail-redirect'),

    re_path(r'^(?P<store>[-\w]+)/category/(?P<slug>[-\w]+)/$',
            views.ProductCategoryView.as_view(), name='product-category'),

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

    path('<str:store>/payment/pp_standard/success/',
         views.PaypalSuccessView.as_view(), name='paypal-return'),

    path('<str:store>/payment/pp_standard/callback/',
         views.PaypalCallbackView.as_view(), name='paypal-notify-url'),

    path('<str:store>/gamemeca/ranking/',
         views.GamemecaRankingView.as_view(), name='gamemeca-ranking'),

    re_path(r'^(?P<store>[-\w]+)/gamemeca/news/(?P<slug>[-\w]+)/$',
            views.GamemecaNewsView.as_view(), name='gamemeca-news'),

    path('sitemap.xml',
         sitemap, {'sitemaps': sitemaps_static}, name='django.contrib.sitemaps.views.sitemap'),

    path('sitemap-product-category.xml',
         sitemap, {'sitemaps': sitemaps_product_category}, name='django.contrib.sitemaps.views.sitemap'),

    path('sitemap-product.xml',
         sitemap, {'sitemaps': sitemaps_product}, name='django.contrib.sitemaps.views.sitemap'),

    path('sitemap-notice-message.xml',
         sitemap, {'sitemaps': sitemaps_notice_message}, name='django.contrib.sitemaps.views.sitemap'),

    path('sitemap-testimonials.xml',
         sitemap, {'sitemaps': sitemaps_testimonials}, name='django.contrib.sitemaps.views.sitemap'),

    path('sitemap-all.xml',
         sitemap, {'sitemaps': sitemaps_all}, name='django.contrib.sitemaps.views.sitemap'),

    path('naver-adcenter.txt',
         views.NaverAdcenterView.as_view(), name='naver-adcenter'),

    path('product.json',
         views.ProductJSONView.as_view(), name='product-json'),
]
