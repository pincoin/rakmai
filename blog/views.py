import logging

from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    DetailView, ListView
)
from django.views.generic.dates import (
    ArchiveIndexView, YearArchiveView, MonthArchiveView, DayArchiveView
)
from django.views.generic.edit import (
    CreateView, UpdateView, DeleteView
)
from ipware.ip import get_ip

from rakmai.viewmixins import (
    SuperuserRequiredMixin, PageableMixin, OwnerRequiredMixin
)
from rakmai.views import (
    FileUploadView, FileDeleteView
)
from . import settings as blog_settings
from .forms import (
    PostForm, PostAttachmentForm
)
from .models import (
    Post, Category, Attachment, Blog
)
from .viewmixins import (
    BlogContextMixin, SearchContextMixin
)


class PostDetailView(SearchContextMixin, BlogContextMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'post'

    def get_object(self, queryset=None):
        obj = super(PostDetailView, self).get_object()
        obj.view_count += 1
        obj.save()
        return obj

    def get_queryset(self):
        return Post.objects \
            .select_related('category', 'owner', 'blog') \
            .blog(self.kwargs['blog']) \
            .published()

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        context['page_title'] = self.object.title
        context['page_meta_description'] = self.object.description
        context['page_meta_keywords'] = self.object.keywords
        context['post_absolute_url'] = self.request.build_absolute_uri(
            reverse('blog:post-detail', args=(self.object.blog.slug, self.object.pk, self.object.slug)))
        return context

    def get_template_names(self):
        return 'blog/{}/post_detail.html'.format(self.blog.theme)


class PostListView(SearchContextMixin, PageableMixin, BlogContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = Post.objects \
            .select_related('category', 'owner', 'blog') \
            .blog(self.kwargs['blog']) \
            .published()

        form = self.search_form_class(self.request.GET)
        if form.is_valid() and form.cleaned_data['q']:
            q = form.cleaned_data['q']
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(excerpt__icontains=q) |
                Q(content__icontains=q)
            )

        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Posts').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_list.html'.format(self.blog.theme)


class PostMyDetailView(SearchContextMixin, BlogContextMixin, DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects \
            .select_related('category', 'owner', 'blog') \
            .blog(self.kwargs['blog'])

    def get_context_data(self, **kwargs):
        context = super(PostMyDetailView, self).get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context

    def get_template_names(self):
        return 'blog/{}/post_my_detail.html'.format(self.blog.theme)


class PostMyListView(SearchContextMixin, PageableMixin, SuperuserRequiredMixin, BlogContextMixin,
                     ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'posts'

    def get_queryset(self):
        # Note: OwnerRequiredMixin cannot be applied because of `self.kwargs['blog']`
        queryset = Post.objects \
            .select_related('category', 'owner', 'blog') \
            .blog(self.kwargs['blog']) \
            .filter(owner=self.request.user)

        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(PostMyListView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} My Blog Posts').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_my_list.html'.format(self.blog.theme)


class PostCreateView(SearchContextMixin, SuperuserRequiredMixin, BlogContextMixin, CreateView):
    logger = logging.getLogger(__name__)
    model = Post
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super(PostCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Write Post').format(self.blog.title)
        return context

    def get_form_class(self):
        """
        Return different form when validation is required.
        Hidden fields are not prepopulated but appended to form by AJAX.
        """
        if self.request.method == 'POST':
            return PostAttachmentForm
        else:
            return PostForm

    def get_form_kwargs(self):
        # Pass 'self.request' object to PostForm instance
        kwargs = super(PostCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['categories'] = self.blog.categories.all()
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Post model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.ip_address = get_ip(self.request)
        form.instance.owner = self.request.user
        form.instance.blog = self.blog

        # The fields such as created, updated, view_count are filled by default.
        response = super(PostCreateView, self).form_valid(form)

        # Retrieve attachments not related to any post yet.
        attachments = Attachment.objects.filter(
            uid__in=form.cleaned_data['attachments'],
            post__isnull=True,
        )

        if attachments:
            self.object.attachments.set(attachments)

        return response

    def get_success_url(self):
        return reverse('blog:post-my-detail', args=(self.blog.slug, self.object.id, self.object.slug))

    def get_template_names(self):
        return 'blog/{}/post_create.html'.format(self.blog.theme)


class PostUpdateView(SearchContextMixin, OwnerRequiredMixin, SuperuserRequiredMixin, BlogContextMixin, UpdateView):
    logger = logging.getLogger(__name__)
    model = Post
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super(PostUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Edit Post - {}').format(self.blog.title, self.object.title)
        return context

    def get_form_class(self):
        """
        Return different form when validation is required.
        Hidden fields are not prepopulated but appended to form by AJAX.
        """
        if self.request.method == 'POST':
            return PostAttachmentForm
        else:
            return PostForm

    def get_form_kwargs(self):
        # Pass 'self.request' object to PostForm instance
        kwargs = super(PostUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['categories'] = self.blog.categories.all()
        return kwargs

    def form_valid(self, form):
        # These must be set before `form_valid()` which saves Post model instance.
        # Then, `self.object` is available in order to save attachments.
        form.instance.ip_address = get_ip(self.request)
        form.instance.owner = self.request.user
        form.instance.blog = self.blog

        # The fields such as created, updated, view_count are filled by default.
        response = super(PostUpdateView, self).form_valid(form)

        # Retrieve attachments not related to any post yet.
        attachments = Attachment.objects.filter(
            uid__in=form.cleaned_data['attachments'],
            post__isnull=True,
        )

        if attachments:
            attachments.update(post=self.object)

        return response

    def get_success_url(self):
        return reverse('blog:post-my-detail', args=(self.blog.slug, self.object.id, self.object.slug))

    def get_template_names(self):
        return 'blog/{}/post_update.html'.format(self.blog.theme)


class PostDeleteView(OwnerRequiredMixin, SuperuserRequiredMixin, BlogContextMixin, DeleteView):
    logger = logging.getLogger(__name__)
    model = Post
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super(PostDeleteView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Delete Post - {}').format(self.blog.title, self.object.title)
        return context

    def get_success_url(self):
        return reverse('blog:post-my-list', args=(self.object.blog.slug,))

    def get_template_names(self):
        return 'blog/{}/post_confirm_delete.html'.format(self.blog.theme)


class PostCategoryView(SearchContextMixin, PageableMixin, BlogContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = Post.objects \
            .blog(self.kwargs['blog']) \
            .published() \
            .select_related('category', 'owner', 'blog') \
            .filter(category__in=Category.objects
                    .filter(slug=self.kwargs['slug'])
                    .get_descendants(include_self=True)
                    .order_by('tree_id', 'lft'))

        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostCategoryView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Posts By Categories').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_list.html'.format(self.blog.theme)


class PostTagView(SearchContextMixin, PageableMixin, BlogContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = Post.objects \
            .blog(self.kwargs['blog']) \
            .published() \
            .select_related('category', 'owner', 'blog') \
            .filter(tags__slug=self.kwargs['slug'])

        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostTagView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Posts By Tags').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_list.html'.format(self.blog.theme)


class TagView(SearchContextMixin, BlogContextMixin, ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'tags'

    def get_queryset(self):
        extra_filters = {
            'post__blog__slug': self.kwargs['blog'],
            'post__status': Post.STATUS_CHOICES.published,
            'post__is_removed': False,
        }

        return Post.tags.most_common(blog_settings.BLOG_MINIMUM_COUNT_OF_TAGS, extra_filters)

    def get_context_data(self, **kwargs):
        context = super(TagView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Tags').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/blog_tags.html'.format(self.blog.theme)


class RssView(Feed):
    logger = logging.getLogger(__name__)
    title = _('Blog RSS')
    link = '/rss'
    description = _('Blog Recent Posts')

    def get_object(self, request, *args, **kwargs):
        return Blog.objects.get(slug=kwargs['blog'])

    def items(self, blog):
        return Post.objects.blog(blog.slug).published().order_by('-published')[:blog.rss_size]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_link(self, item):
        return reverse('blog:post-detail', args=[item.blog.slug, item.pk, item.slug])


class PostArchiveIndexView(SearchContextMixin, PageableMixin, BlogContextMixin, ArchiveIndexView):
    context_object_name = 'posts'
    date_field = 'published'

    def get_queryset(self):
        queryset = Post.objects.select_related('blog').blog(self.kwargs['blog']).published()
        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostArchiveIndexView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Archive').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_archive.html'.format(self.blog.theme)


class PostYearArchiveView(SearchContextMixin, PageableMixin, BlogContextMixin, YearArchiveView):
    context_object_name = 'posts'
    date_field = 'published'
    make_object_list = True

    def get_queryset(self):
        queryset = Post.objects \
            .select_related('blog') \
            .blog(self.kwargs['blog']) \
            .published()
        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostYearArchiveView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Yearly Archive').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_archive_year.html'.format(self.blog.theme)


class PostMonthArchiveView(SearchContextMixin, PageableMixin, BlogContextMixin, MonthArchiveView):
    context_object_name = 'posts'
    date_field = 'published'

    def get_queryset(self):
        queryset = Post.objects \
            .select_related('blog') \
            .blog(self.kwargs['blog']) \
            .published()
        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostMonthArchiveView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Monthly Archive').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_archive_month.html'.format(self.blog.theme)


class PostDayArchiveView(SearchContextMixin, PageableMixin, BlogContextMixin, DayArchiveView):
    context_object_name = 'posts'
    date_field = 'published'

    def get_queryset(self):
        queryset = Post.objects \
            .select_related('blog') \
            .blog(self.kwargs['blog']) \
            .published()
        return queryset.order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(PostDayArchiveView, self).get_context_data(**kwargs)
        context['page_title'] = _('{} Blog Daily Archive').format(self.blog.title)
        return context

    def get_template_names(self):
        return 'blog/{}/post_archive_day.html'.format(self.blog.theme)


class PostAttachmentUploadView(SuperuserRequiredMixin, FileUploadView):
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


class PostAttachmentDeleteView(SuperuserRequiredMixin, FileDeleteView):
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
            attachment = Attachment.objects.select_related('post__owner').get(uid=form.cleaned_data['uid'])

            if attachment.post and attachment.post.owner == user:
                attachment.post = None
                attachment.save()

            files.append({
                "uid": attachment.uid,
            })

        # Return JSON key `files`
        return {"files": files}
