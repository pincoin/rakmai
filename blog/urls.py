from django.contrib.sitemaps.views import sitemap
from django.urls import (
    path, re_path
)

from .sitemaps import PostSitemap
from .views import (
    PostListView, PostDetailView, PostMyListView, PostMyDetailView, PostCreateView, PostUpdateView, PostDeleteView,
    PostCategoryView, PostTagView, TagView, RssView,
    PostArchiveIndexView, PostYearArchiveView, PostMonthArchiveView, PostDayArchiveView,
    PostAttachmentUploadView, PostAttachmentDeleteView,
)

sitemaps_post = {
    'sitemap': PostSitemap(),
}

app_name = 'blog'

urlpatterns = [
    path('<str:blog>/posts/',
         PostListView.as_view(), name='post-list'),

    re_path(r'^(?P<blog>[-\w]+)/(?P<pk>\d+)/(?P<slug>[-\w]+)/$',
            PostDetailView.as_view(), name='post-detail'),

    path('<str:blog>/posts/me/',
         PostMyListView.as_view(), name='post-my-list'),

    re_path(r'^(?P<blog>[-\w]+)/posts/me/(?P<pk>\d+)/(?P<slug>[-\w]+)/$',
            PostMyDetailView.as_view(), name='post-my-detail'),

    path('<str:blog>/posts/me/new/',
         PostCreateView.as_view(), name='post-create'),

    re_path(r'^(?P<blog>[-\w]+)/posts/me/(?P<pk>\d+)/(?P<slug>[-\w]+)/edit$',
            PostUpdateView.as_view(), name='post-edit'),

    re_path(r'^(?P<blog>[-\w]+)/posts/me/(?P<pk>\d+)/(?P<slug>[-\w]+)/delete$',
            PostDeleteView.as_view(), name='post-delete'),

    re_path(r'^(?P<blog>[-\w]+)/category/(?P<slug>[-\w]+)/$',
            PostCategoryView.as_view(), name='post-category'),

    re_path(r'^(?P<blog>[-\w]+)/tags/(?P<slug>[-\w]+)/$',
            PostTagView.as_view(), name='post-tag'),

    path('<str:blog>/tags/',
         TagView.as_view(), name='tag'),

    path('<str:blog>/rss/',
         RssView(), name='rss'),

    path('<str:blog>/archive/',
         PostArchiveIndexView.as_view(), name='post-archive'),

    path('<str:blog>/archive/<int:year>/',
         PostYearArchiveView.as_view(), name='post-archive-year'),

    path('<str:blog>/archive/<int:year>/<int:month>/',
         PostMonthArchiveView.as_view(month_format='%m'), name='post-archive-month'),

    path('<str:blog>/archive/<int:year>/<int:month>/<int:day>/',
         PostDayArchiveView.as_view(month_format='%m'), name='post-archive-day'),

    path('sitemap-posts.xml',
         sitemap, {'sitemaps': sitemaps_post}, name='django.contrib.sitemaps.views.sitemap'),

    path('upload-file',
         PostAttachmentUploadView.as_view(), name='post-file-upload'),

    path('delete-file',
         PostAttachmentDeleteView.as_view(), name='post-file-delete'),
]
