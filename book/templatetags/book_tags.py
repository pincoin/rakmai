from django import template
from mptt.utils import get_cached_trees

from ..models import Page

register = template.Library()


class PageNode():
    def __init__(self, tree_query_set, indent):
        self.tree_query_set = tree_query_set
        self.indent = indent

    def _get_children(self, page_item):
        page_item.indent = self.indent * (page_item.level + 1)

        nodes = [page_item]

        for child in page_item.get_children():
            nodes.extend(self._get_children(child))

        return nodes

    def get_list(self):
        nodes = []

        for page_item in self.tree_query_set:
            nodes.extend(self._get_children(page_item))

        return nodes


@register.simple_tag
def get_table_of_contents(book_id, indent):
    tree_set = get_cached_trees(Page.objects.select_related('book').filter(book__pk=book_id).order_by('tree_id', 'lft'))
    tree_list = PageNode(tree_set, indent).get_list()

    return {
        'tree_set': tree_set,
        'tree_list': tree_list,
    }


@register.simple_tag
def get_adjacent_pages(book_id, page_id):
    tree_set = get_cached_trees(Page.objects.select_related('book').filter(book__pk=book_id).order_by('tree_id', 'lft'))
    tree_list = PageNode(tree_set, 0).get_list()

    i = 0
    for i, p in enumerate(tree_list):
        if p.id == page_id:
            break

    return {
        'previous_page': tree_list[i - 1] if i > 0 else None,
        'next_page': tree_list[i + 1] if i + 1 < len(tree_list) else None,
    }


@register.simple_tag
def get_first_page(book_id):
    return Page.objects.select_related('book').filter(book__pk=book_id).order_by('tree_id', 'lft').first()


@register.simple_tag
def get_ancestor_path(page_id):
    return get_cached_trees(Page.objects.get(pk=page_id).get_ancestors(include_self=False).order_by('tree_id', 'lft'))
