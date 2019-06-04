import logging

from .forms import PageSearchForm
from .models import Book


class BookContextMixin(object):
    logger = logging.getLogger(__name__)

    def dispatch(self, *args, **kwargs):
        self.book = Book.objects.get(pk=self.kwargs.get('book'))

        return super(BookContextMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookContextMixin, self).get_context_data(**kwargs)
        context['book'] = self.book
        return context


class SearchContextMixin(object):
    logger = logging.getLogger(__name__)

    search_form_class = PageSearchForm

    def get_context_data(self, **kwargs):
        context = super(SearchContextMixin, self).get_context_data(**kwargs)

        context['search_form'] = self.search_form_class(
            q=self.request.GET.get('q') if self.request.GET.get('q') else '')

        return context
