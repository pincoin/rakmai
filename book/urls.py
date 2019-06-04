from django.contrib.sitemaps.views import sitemap
from django.urls import path

from .sitemaps import PageSitemap
from .views import (
    BookListView, BookDetailView, BookMyListView, BookMyDetailView, BookCreateView, BookUpdateView, BookDeleteView,
    PageDetailView, PageListView, PageCreateView, PageUpdateView, PageDeleteView, PageMyDetailView, PageMyListView,
    PageAttachmentUploadView, PageAttachmentDeleteView
)

sitemaps_page = {
    'sitemap': PageSitemap(),
}

app_name = 'book'

urlpatterns = [
    path('',
         BookListView.as_view(), name='book-list'),

    path('<int:pk>/',
         BookDetailView.as_view(), name='book-detail'),

    path('<int:book>/<int:pk>/',
         PageDetailView.as_view(), name='page-detail'),

    path('<int:book>/list/',
         PageListView.as_view(), name='page-list'),

    path('me/',
         BookMyListView.as_view(), name='book-my-list'),

    path('me/<int:pk>/',
         BookMyDetailView.as_view(), name='book-my-detail'),

    path('me/new/',
         BookCreateView.as_view(), name='book-create'),

    path('me/<int:pk>/edit',
         BookUpdateView.as_view(), name='book-edit'),

    path('me/<int:pk>/delete',
         BookDeleteView.as_view(), name='book-delete'),

    path('me/<int:book>/<int:pk>/',
         PageMyDetailView.as_view(), name='page-my-detail'),

    path('me/<int:book>/list/',
         PageMyListView.as_view(), name='page-my-list'),

    path('me/<int:book>/new/',
         PageCreateView.as_view(), name='page-create'),

    path('me/<int:book>/<int:pk>/edit',
         PageUpdateView.as_view(), name='page-edit'),

    path('me/<int:book>/<int:pk>/delete',
         PageDeleteView.as_view(), name='page-delete'),

    path('sitemap-pages.xml',
         sitemap, {'sitemaps': sitemaps_page}, name='django.contrib.sitemaps.views.sitemap'),

    path('upload-file',
         PageAttachmentUploadView.as_view(), name='page-file-upload'),

    path('delete-file',
         PageAttachmentDeleteView.as_view(), name='page-file-delete'),

    # /book/category
]
