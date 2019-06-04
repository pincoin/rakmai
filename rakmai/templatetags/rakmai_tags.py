from django import template
from django.utils.safestring import mark_safe
from mptt.utils import get_cached_trees

from ..helpers import (
    get_sub_domain, get_domain, get_domains
)
from ..models import (
    MenuItem, Google
)

register = template.Library()


class NavbarNode(template.Node):
    def __init__(self, nodes, tree_query_set):
        self.nodes = nodes
        self.tree_query_set = get_cached_trees(tree_query_set)
        self.request = template.Variable('request')

    def _render_menu_item(self, context, menu_item):
        request = self.request.resolve(context)

        nodes = []
        context.push()

        for child in menu_item.get_children():
            nodes.append(self._render_menu_item(context, child))

        menu_item.active = False

        if menu_item.match == 'equals' and request.path == menu_item.url \
                or menu_item.match == 'startswith' and request.path.startswith(menu_item.url):
            menu_item.active = True

        context['menu_item'] = menu_item
        context['children'] = mark_safe(''.join(nodes))

        rendered = self.nodes.render(context)

        context.pop()
        return rendered

    def render(self, context):
        nodes = [self._render_menu_item(context, menu_item) for menu_item in self.tree_query_set]
        return ''.join(nodes)


@register.tag
def navbar(parser, token):
    # separates the arguments on spaces while keeping quoted strings together
    tokens = token.split_contents()

    if len(tokens) != 2:
        raise template.TemplateSyntaxError('{} tag requires a tree queryset.'.format(tokens[0]))

    nodes = parser.parse(('end_navbar',))
    parser.delete_first_token()

    try:
        tree_query_set = MenuItem.objects \
            .get(title=tokens[1][1:-1]) \
            .get_descendants(include_self=False)\
            .order_by('tree_id', 'lft')
    except MenuItem.DoesNotExist:
        tree_query_set = None

    return NavbarNode(nodes, tree_query_set)


class GoogleAnalyticsNode(template.Node):
    def __init__(self, uid, template_name):
        self.uid = uid
        self.template_name = template_name

    def render(self, context):
        t = context.template.engine.get_template(self.template_name)
        return t.render(
            template.Context({
                'uid': self.uid
            }, autoescape=context.autoescape))


@register.tag
def google_analytics(parser, token):
    template_name = 'rakmai/google_analytics.html'

    tokens = token.split_contents()
    num = len(tokens)

    if num != 2:
        raise template.TemplateSyntaxError('%r tag requires site ID.' % tokens[0])

    try:
        g = Google.objects.get(site_id=tokens[1][1:-1])
        uid = g.analytics_uid
    except Google.DoesNotExist:
        uid = None

    return GoogleAnalyticsNode(uid, template_name)


@register.simple_tag(takes_context=True)
def sub_domain(context):
    return get_sub_domain(context['request'])


@register.simple_tag(takes_context=True)
def domain(context):
    return get_domain(context['request'])


@register.simple_tag(takes_context=True)
def domains(context):
    return get_domains(context['request'])
