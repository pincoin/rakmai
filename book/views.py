import logging

from django.db.models import Q
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    ListView, DetailView
)
from django.views.generic.edit import (
    CreateView, UpdateView, DeleteView
)
from ipware.ip import get_ip

from rakmai.viewmixins import (
    SuperuserRequiredMixin, OwnerRequiredMixin, PageableMixin
)
from rakmai.views import (
    FileUploadView, FileDeleteView
)
from . import settings as book_settings
from .forms import (
    BookForm, PageForm, PageAttachmentForm
)
from .models import (
    Book, Page, Category, Attachment
)
from .viewmixins import (
    BookContextMixin, SearchContextMixin
)


class BookListView(SearchContextMixin, PageableMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'books'

    def __init__(self):
        super(BookListView, self).__init__()
        self.block_size = book_settings.BOOK_BLOCK_SIZE
        self.chunk_size = book_settings.BOOK_CHUNK_SIZE

    def get_queryset(self):
        return Book.objects \
            .select_related('category', 'owner') \
            .public()

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Book List')
        return context

    def get_template_names(self):
        return 'book/{}/book_list.html'.format(book_settings.BOOK_THEME)


class BookDetailView(SearchContextMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'book'

    def get_object(self, queryset=None):
        obj = super(BookDetailView, self).get_object()
        obj.view_count += 1
        obj.save()
        return obj

    def get_queryset(self):
        return Book.objects \
            .select_related('category', 'owner') \
            .filter(pk=self.kwargs['pk']) \
            .public()

    def get_context_data(self, **kwargs):
        context = super(BookDetailView, self).get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context

    def get_template_names(self):
        return 'book/{}/book_detail.html'.format(book_settings.BOOK_THEME)


class BookMyListView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, PageableMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'books'
    queryset = Book.objects \
        .select_related('category', 'owner')

    def __init__(self):
        super(BookMyListView, self).__init__()
        self.block_size = book_settings.BOOK_BLOCK_SIZE
        self.chunk_size = book_settings.BOOK_CHUNK_SIZE

    def get_queryset(self):
        # Note: Call OwnerRequiredMixin
        return super(BookMyListView, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(BookMyListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Book List')
        return context

    def get_template_names(self):
        return 'book/{}/book_my_list.html'.format(book_settings.BOOK_THEME)


class PageDetailView(SearchContextMixin, BookContextMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'page'

    def get_object(self, queryset=None):
        obj = super(PageDetailView, self).get_object()
        obj.view_count += 1
        obj.save()
        return obj

    def get_queryset(self):
        return Page.objects.filter(pk=self.kwargs['pk']) \
            .select_related('owner', 'book') \
            .book(self.kwargs['book']) \
            .filter(book__status=Book.STATUS_CHOICES.public) \
            .public() \
            .order_by('tree_id', 'lft')

    def get_context_data(self, **kwargs):
        context = super(PageDetailView, self).get_context_data(**kwargs)
        context['page_title'] = '{} - {}'.format(self.object.title, self.object.book.title)
        context['page_meta_description'] = self.object.description
        context['page_meta_keywords'] = self.object.keywords
        context['page_id'] = int(self.kwargs['pk'])
        context['page_absolute_url'] = self.request.build_absolute_uri(
            reverse('book:page-detail', args=(self.object.book.pk, self.object.pk)))
        return context

    def get_form_kwargs(self):
        return {
            'book': self.object.book.id,
            'page': self.object.id,
        }

    def get_template_names(self):
        return 'book/{}/page_detail.html'.format(book_settings.BOOK_THEME)


class PageListView(SearchContextMixin, BookContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'pages'

    def get_queryset(self):
        queryset = Page.objects \
            .book(self.kwargs['book']) \
            .public() \
            .order_by('tree_id', 'lft')

        form = self.search_form_class(self.request.GET)
        if form.is_valid() and form.cleaned_data['q']:
            q = form.cleaned_data['q']
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q)
            )
            return queryset
        else:
            return None

    def get_context_data(self, **kwargs):
        context = super(PageListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Search Results - {}').format(self.book.title)
        return context

    def get_template_names(self):
        return 'book/{}/page_list.html'.format(book_settings.BOOK_THEME)


class BookMyDetailView(SearchContextMixin, SuperuserRequiredMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'book'

    def get_queryset(self):
        return Book.objects \
            .select_related('category', 'owner') \
            .filter(pk=self.kwargs['pk']) \
            .filter(owner=self.request.user)  # No OwnerRequiredMixin

    def get_context_data(self, **kwargs):
        context = super(BookMyDetailView, self).get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context

    def get_template_names(self):
        return 'book/{}/book_my_detail.html'.format(book_settings.BOOK_THEME)


class BookCreateView(SearchContextMixin, SuperuserRequiredMixin, CreateView):
    logger = logging.getLogger(__name__)
    model = Book
    context_object_name = 'book'
    form_class = BookForm

    def get_context_data(self, **kwargs):
        context = super(BookCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Write New Book')
        return context

    def get_form_kwargs(self):
        kwargs = super(BookCreateView, self).get_form_kwargs()
        kwargs['categories'] = Category.objects.all().order_by('tree_id', 'lft')
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Page model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.owner = self.request.user
        form.instance.view_count = 0
        form.instance.updated = now()

        return super(BookCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('book:book-my-detail', args=(self.object.id,))

    def get_template_names(self):
        return 'book/{}/book_create.html'.format(book_settings.BOOK_THEME)


class BookUpdateView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, UpdateView):
    logger = logging.getLogger(__name__)
    model = Book
    context_object_name = 'book'
    form_class = BookForm

    def get_context_data(self, **kwargs):
        context = super(BookUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Edit Book - {}').format(self.object.title)
        return context

    def get_form_kwargs(self):
        kwargs = super(BookUpdateView, self).get_form_kwargs()
        kwargs['categories'] = Category.objects.all().order_by('tree_id', 'lft')
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Page model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.updated = now()

        # The fields such as created, updated, view_count are filled by default.
        return super(BookUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('book:book-my-detail', args=(self.object.id,))

    def get_template_names(self):
        return 'book/{}/book_update.html'.format(book_settings.BOOK_THEME)


class BookDeleteView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, DeleteView):
    logger = logging.getLogger(__name__)
    model = Book
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super(BookDeleteView, self).get_context_data(**kwargs)
        context['page_title'] = _('Delete Book - {}').format(self.object.title)
        return context

    def get_success_url(self):
        return reverse('book:book-my-list')

    def get_template_names(self):
        return 'book/{}/book_confirm_delete.html'.format(book_settings.BOOK_THEME)


class PageCreateView(SearchContextMixin, SuperuserRequiredMixin, BookContextMixin, CreateView):
    logger = logging.getLogger(__name__)
    model = Page
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        context = super(PageCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Write New Page')
        return context

    def get_form_class(self):
        """
        Return different form when validation is required.
        Hidden fields are not prepopulated but appended to form by AJAX.
        """
        if self.request.method == 'POST':
            return PageAttachmentForm
        else:
            return PageForm

    def get_form_kwargs(self):
        kwargs = super(PageCreateView, self).get_form_kwargs()
        kwargs['parents'] = Page.objects.filter(book__pk=self.book.pk).order_by('tree_id', 'lft')
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Page model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.book = self.book
        form.instance.book.updated = now()
        form.instance.book.save()
        form.instance.owner = self.request.user
        form.instance.view_count = 0
        form.instance.updated = now()
        form.instance.ip_address = get_ip(self.request)

        response = super(PageCreateView, self).form_valid(form)

        # Retrieve attachments not related to any post yet.
        attachments = Attachment.objects.filter(
            uid__in=form.cleaned_data['attachments'],
            page__isnull=True,
        )

        if attachments:
            self.object.attachments.set(attachments)

        return response

    def get_success_url(self):
        return reverse('book:page-my-detail', args=(self.book.id, self.object.id))

    def get_template_names(self):
        return 'book/{}/page_create.html'.format(book_settings.BOOK_THEME)


class PageUpdateView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, BookContextMixin, UpdateView):
    logger = logging.getLogger(__name__)
    model = Page
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        context = super(PageUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Edit Page - {}').format(self.object.title)
        return context

    def get_form_class(self):
        """
        Return different form when validation is required.
        Hidden fields are not prepopulated but appended to form by AJAX.
        """
        if self.request.method == 'POST':
            return PageAttachmentForm
        else:
            return PageForm

    def get_form_kwargs(self):
        kwargs = super(PageUpdateView, self).get_form_kwargs()
        kwargs['parents'] = Page.objects.filter(book__pk=self.book.pk).order_by('tree_id', 'lft')
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Page model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.book.updated = now()
        form.instance.book.save()
        form.instance.updated = now()
        form.instance.ip_address = get_ip(self.request)

        response = super(PageUpdateView, self).form_valid(form)

        # Retrieve attachments not related to any post yet.
        attachments = Attachment.objects.filter(
            uid__in=form.cleaned_data['attachments'],
            page__isnull=True,
        )

        if attachments:
            attachments.update(page=self.object)

        return response

    def get_success_url(self):
        return reverse('book:page-my-detail', args=(self.book.id, self.object.id))

    def get_template_names(self):
        return 'book/{}/page_update.html'.format(book_settings.BOOK_THEME)


class PageDeleteView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, BookContextMixin, DeleteView):
    logger = logging.getLogger(__name__)
    model = Page
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        context = super(PageDeleteView, self).get_context_data(**kwargs)
        context['page_title'] = _('Delete Page - {}').format(self.object.title)
        return context

    def get_success_url(self):
        return reverse('book:book-my-detail', args=(self.book.id,))

    def get_template_names(self):
        return 'book/{}/page_confirm_delete.html'.format(book_settings.BOOK_THEME)


class PageMyDetailView(SearchContextMixin, SuperuserRequiredMixin, BookContextMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'page'

    def get_queryset(self):
        # No OwnerRequiredMixin
        return Page.objects \
            .filter(pk=self.kwargs['pk']) \
            .select_related('owner', 'book') \
            .book(self.kwargs['book']) \
            .filter(owner=self.request.user) \
            .order_by('tree_id', 'lft')

    def get_context_data(self, **kwargs):
        context = super(PageMyDetailView, self).get_context_data(**kwargs)
        context['page_title'] = '{} - {}'.format(self.object.title, self.object.book.title)
        context['page_meta_description'] = self.object.description
        context['page_meta_keywords'] = self.object.keywords
        context['page_id'] = int(self.kwargs['pk'])
        return context

    def get_template_names(self):
        return 'book/{}/page_my_detail.html'.format(book_settings.BOOK_THEME)


class PageMyListView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, BookContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'pages'

    def get_queryset(self):
        # No OwnerRequiredMixin
        queryset = Page.objects \
            .book(self.kwargs['book']) \
            .filter(owner=self.request.user) \
            .order_by('tree_id', 'lft')

        form = self.search_form_class(self.request.GET)
        if form.is_valid() and form.cleaned_data['q']:
            q = form.cleaned_data['q']
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q)
            )
            return queryset
        else:
            return None

    def get_context_data(self, **kwargs):
        context = super(PageMyListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Search Results - {}').format(self.book.title)
        return context

    def get_template_names(self):
        return 'book/{}/page_my_list.html'.format(book_settings.BOOK_THEME)


class PageAttachmentUploadView(SuperuserRequiredMixin, FileUploadView):
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


class PageAttachmentDeleteView(SuperuserRequiredMixin, FileDeleteView):
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
            attachment = Attachment.objects.select_related('page__owner').get(uid=form.cleaned_data['uid'])

            if attachment.page and attachment.page.owner == user:
                attachment.page = None
                attachment.save()

            files.append({
                "uid": attachment.uid,
            })

        # Return JSON key `files`
        return {"files": files}
