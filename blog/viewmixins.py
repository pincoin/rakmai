import logging

from .forms import PostSearchForm
from .models import Blog


class BlogContextMixin(object):
    logger = logging.getLogger(__name__)

    def dispatch(self, *args, **kwargs):
        self.blog = Blog.objects.get(slug=self.kwargs['blog'])

        self.block_size = self.blog.block_size
        self.chunk_size = self.blog.chunk_size

        return super(BlogContextMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BlogContextMixin, self).get_context_data(**kwargs)
        context['blog'] = self.blog
        return context


class SearchContextMixin(object):
    logger = logging.getLogger(__name__)

    search_form_class = PostSearchForm

    def get_context_data(self, **kwargs):
        context = super(SearchContextMixin, self).get_context_data(**kwargs)

        context['search_form'] = self.search_form_class(
            q=self.request.GET.get('q') if self.request.GET.get('q') else '')

        return context
