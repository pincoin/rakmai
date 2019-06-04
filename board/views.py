import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.views.generic import (
    ListView, DetailView
)
from django.views.generic.edit import (
    CreateView, UpdateView, DeleteView
)
from ipware.ip import get_ip

from rakmai.viewmixins import (
    PageableMixin, OwnerRequiredMixin
)
from rakmai.views import (
    FileUploadView, FileDeleteView
)
from .forms import (
    MessageForm, MessageAttachmentForm, MessageSearchForm
)
from .models import (
    Message, Attachment
)
from .viewmixins import BoardContextMixin


class MessageListView(PageableMixin, BoardContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'messages'
    form_class = MessageSearchForm

    def __init__(self):
        super(MessageListView, self).__init__()

    def get_queryset(self):
        form = self.form_class(self.request.GET)

        queryset = Message.objects \
            .select_related('owner', 'board') \
            .board(self.kwargs['slug']) \
            .published()

        if form.is_valid():
            where = form.cleaned_data['where']
            q = form.cleaned_data['q']

            queryset = queryset.public()  # search only in public messages

            if where == form.TITLE:
                queryset = queryset.filter(Q(title__icontains=q) | Q(content__icontains=q))
            elif where == form.CONTENT:
                queryset = queryset.filter(Q(content__icontains=q))
            elif where == form.TITLE_CONTENT:
                queryset = queryset.filter(Q(title__icontains=q) | Q(content__icontains=q))
            elif where == form.NICKNAME:
                queryset = queryset.filter(Q(nickname__icontains=q))

        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(MessageListView, self).get_context_data(**kwargs)
        context['board'] = self.board  # Fetched by BoardContextMixin.dispatch()
        context['message_search_form'] = self.form_class  # Class is ok not instance.
        return context

    def get_template_names(self):
        return 'board/{}/message_list.html'.format(self.board.theme)


class MessageDetailView(BoardContextMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'message'

    def get_object(self, queryset=None):
        o = super(MessageDetailView, self).get_object()
        o.view_count += 1
        o.save()
        return o

    def get_queryset(self):
        return Message.objects.published() \
            .select_related('owner', 'board') \
            .board(self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super(MessageDetailView, self).get_context_data(**kwargs)
        context['board'] = self.board
        return context

    def get_template_names(self):
        return 'board/{}/message_detail.html'.format(self.board.theme)


class MessageMyListView(PageableMixin, BoardContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'messages'
    form_class = MessageSearchForm

    def __init__(self):
        super(MessageMyListView, self).__init__()

    def get_queryset(self):
        return Message.objects \
            .select_related('owner', 'board') \
            .board(self.kwargs['slug']) \
            .published() \
            .order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(MessageMyListView, self).get_context_data(**kwargs)
        context['board'] = self.board  # Fetched by BoardContextMixin.dispatch()
        context['message_search_form'] = self.form_class  # Class is ok not instance.
        return context

    def get_template_names(self):
        return 'board/{}/message_my_list.html'.format(self.board.theme)


class MessageCreateView(LoginRequiredMixin, BoardContextMixin, CreateView):
    logger = logging.getLogger(__name__)
    model = Message
    context_object_name = 'message'

    def get_context_data(self, **kwargs):
        context = super(MessageCreateView, self).get_context_data(**kwargs)
        context['board'] = self.board
        return context

    def get_form_class(self):
        """
        Return different form when validation is required.
        Hidden fields are not prepopulated but appended to form by AJAX.
        """
        if self.request.method == 'POST':
            return MessageAttachmentForm
        else:
            return MessageForm

    def get_form_kwargs(self):
        # Pass 'self.request' object to MessageForm instance
        kwargs = super(MessageCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['categories'] = self.board.categories.all()
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Message model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.board = self.board
        form.instance.ip_address = get_ip(self.request)
        form.instance.owner = self.request.user

        # The fields such as created, updated, status, view_count are filled by default.
        response = super(MessageCreateView, self).form_valid(form)

        # Retrieve attachments not related to any message yet.
        attachments = Attachment.objects.filter(
            uid__in=form.cleaned_data['attachments'],
            message__isnull=True,
        )

        if attachments:
            self.object.attachments.set(attachments)

        return response

    def get_success_url(self):
        return reverse('board:message-detail', args=(self.object.board.slug, self.object.id,))

    def get_template_names(self):
        return 'board/{}/message_create.html'.format(self.board.theme)


class MessageUpdateView(OwnerRequiredMixin, LoginRequiredMixin, BoardContextMixin, UpdateView):
    logger = logging.getLogger(__name__)
    model = Message
    context_object_name = 'message'

    def get_form_class(self):
        """
        Return different form when validation is required.
        Hidden fields are not prepopulated but appended to form by AJAX.
        """
        if self.request.method == 'POST':
            return MessageAttachmentForm
        else:
            return MessageForm

    def get_form_kwargs(self):
        # Pass 'self.request' object to MessageForm instance
        kwargs = super(MessageUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['categories'] = self.board.categories.all()
        return kwargs

    def form_valid(self, form):
        response = super(MessageUpdateView, self).form_valid(form)

        # Retrieve attachments not related to any message yet.
        attachments = Attachment.objects.filter(
            uid__in=form.cleaned_data['attachments'],
            message__isnull=True,
        )

        if attachments:
            attachments.update(message=self.object)

        return response

    def get_success_url(self):
        return reverse('board:message-detail', args=(self.object.board.slug, self.object.id,))

    def get_template_names(self):
        return 'board/{}/message_update.html'.format(self.board.theme)


class MessageDeleteView(OwnerRequiredMixin, LoginRequiredMixin, BoardContextMixin, DeleteView):
    logger = logging.getLogger(__name__)
    model = Message
    context_object_name = 'message'

    def get_context_data(self, **kwargs):
        context = super(MessageDeleteView, self).get_context_data(**kwargs)
        context['board'] = self.board  # Fetched by BoardContextMixin.dispatch()
        return context

    def get_success_url(self):
        return reverse('board:message-list', args=(self.object.board.slug,))

    def get_template_names(self):
        return 'board/{}/message_confirm_delete.html'.format(self.board.theme)


class MessageAttachmentUploadView(LoginRequiredMixin, FileUploadView):
    # Raise PermissionDenied exception instead of the redirect
    raise_exception = True

    def upload_file(self, *args, **kwargs):
        """
        Upload files and return JSON file list.
        """
        uploaded_files = kwargs.pop('uploaded_files', None)
        files = []

        if uploaded_files:
            # `files` is HTML attribute name not from Django/Python.
            for file in uploaded_files.getlist('files'):
                # Attachment class inherits AbstractAttachment
                attachment = Attachment()
                attachment.file = file
                attachment.name = file.name
                attachment.save()

                files.append({
                    "uid": attachment.uid,
                    "name": file.name,
                    "size": file.size,
                    "url": attachment.file.url
                })

        # Return JSON key `files`
        return {"files": files}


class MessageAttachmentDeleteView(LoginRequiredMixin, FileDeleteView):
    # Raise PermissionDenied exception instead of the redirect
    raise_exception = True

    def delete_file(self, *args, **kwargs):
        """
        Delete files and return JSON file list.
        """
        form = kwargs.pop('form', None)
        user = kwargs.pop('user', None)

        files = []

        if form and user:
            # Attachment class inherits AbstractAttachment and they are asynchronously deleted by cron.
            attachment = Attachment.objects.select_related('message__owner').get(uid=form.cleaned_data['uid'])

            if attachment.message and attachment.message.owner == user:
                attachment.message = None
                attachment.save()

            files.append({
                "uid": attachment.uid,
            })

        # Return JSON key `files`
        return {"files": files}
