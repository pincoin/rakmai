from django.urls import (
    path, re_path
)

from .views import (
    MessageListView, MessageDetailView, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MessageAttachmentUploadView, MessageAttachmentDeleteView
)

app_name = 'board'

urlpatterns = [
    re_path(r'^(?P<slug>[-\w]+)/$',
            MessageListView.as_view(), name='message-list'),

    re_path(r'^(?P<slug>[-\w]+)/(?P<pk>\d+)/$',
            MessageDetailView.as_view(), name='message-detail'),

    re_path(r'^(?P<slug>[-\w]+)/me$',
            MessageListView.as_view(), name='message-my-list'),

    re_path(r'^(?P<slug>[-\w]+)/me/new/$',
            MessageCreateView.as_view(), name='message-new'),

    re_path(r'^(?P<slug>[-\w]+)/me/(?P<pk>\d+)/edit/$',
            MessageUpdateView.as_view(), name='message-edit'),

    re_path(r'^(?P<slug>[-\w]+)/me/(?P<pk>\d+)/delete/$',
            MessageDeleteView.as_view(), name='message-delete'),

    path('upload-file',
         MessageAttachmentUploadView.as_view(), name='message-file-upload'),

    path('delete-file',
         MessageAttachmentDeleteView.as_view(), name='message-file-delete'),
]
