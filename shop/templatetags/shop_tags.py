from django import template
from django.conf import settings
from django.core.cache import cache
from django.template import Variable
from django.utils.safestring import mark_safe
from mptt.utils import get_cached_trees

from .. import settings as shop_settings
from ..helpers import Cart
from ..models import (
    Product, Category
)

register = template.Library()


class CategoryNode(template.Node):
    def __init__(self, nodes, roots):
        self.nodes = nodes
        self.roots = Variable(roots)
        self.tree_query_set = None

    def _render_category(self, context, category):
        nodes = []
        context.push()

        for child in category.get_children():
            nodes.append(self._render_category(context, child))

        context['category'] = category
        context['children'] = mark_safe(''.join(nodes))

        rendered = self.nodes.render(context)

        context.pop()
        return rendered

    def render(self, context):
        roots = self.roots.resolve(context)
        nodes = [self._render_category(context, category) for category in roots]
        return ''.join(nodes)


@register.tag
def navbar_categories(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, roots = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            '{} tag does not require an additional argument.'.format(token.split_contents()[0])
        )

    nodes = parser.parse(('end_navbar_categories',))
    parser.delete_first_token()

    return CategoryNode(nodes, roots)


@register.simple_tag
def get_category_roots(store_code, pg=False):
    cache_key = 'shop.templatetags.shop_tags.get_category_roots({},{})'.format(store_code, pg)
    cache_time = settings.CACHES['default']['TIMEOUT']

    roots = cache.get(cache_key)

    if not roots:
        try:
            categories = Category.objects.filter(store__code=store_code).order_by('tree_id', 'lft')

            if pg:
                categories = categories.filter(pg=pg)

            roots = get_cached_trees(categories)
            cache.set(cache_key, roots, cache_time)
        except Category.DoesNotExist:
            roots = None

    return roots


@register.simple_tag
def get_product_list(store_code, productlist_code):
    cache_key = 'shop.templatetags.shop_tags.get_product_list({},{})'.format(store_code, productlist_code)
    cache_time = settings.CACHES['default']['TIMEOUT']

    products = cache.get(cache_key)

    if not products:
        products = Product.objects \
            .store(store_code) \
            .enabled() \
            .select_related('category') \
            .filter(productlist__code=productlist_code) \
            .order_by('productlistmembership__position')

        cache.set(cache_key, products, cache_time)

    return products


@register.simple_tag
def get_ancestor_path(category_id):
    return get_cached_trees(Category.objects.get(pk=category_id).get_ancestors(include_self=False))


@register.simple_tag(takes_context=True)
def get_cart(context):
    return Cart(context['request'].session, shop_settings.CART_SESSION_KEY)


@register.simple_tag(takes_context=True)
def get_card_cart(context):
    return Cart(context['request'].session, shop_settings.CARD_CART_SESSION_KEY)


@register.simple_tag(takes_context=True)
def get_cart_item(context, product_pk):
    cart = Cart(context['request'].session, shop_settings.CART_SESSION_KEY)
    return cart.get_item(product_pk)


@register.simple_tag
def get_category_leaf(store_code, pg=False):
    cache_key = 'shop.templatetags.shop_tags.get_category_leaf({},{})'.format(store_code, pg)

    cache_time = settings.CACHES['default']['TIMEOUT']

    categories = cache.get(cache_key)

    if not categories:
        if pg:
            categories = Category.objects \
                .filter(store__code=store_code, level__gt=0, pg=True) \
                .order_by('-pg_discount_rate', '-title')
        else:
            categories = Category.objects \
                .filter(store__code=store_code, level__gt=0) \
                .order_by('-discount_rate', '-title')

        cache.set(cache_key, categories, cache_time)

    return categories
