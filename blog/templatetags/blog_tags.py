from django import template
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.template import Variable
from django.utils.safestring import mark_safe
from mptt.utils import get_cached_trees

from ..models import (
    Post, Category
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
def navbar_blog_categories(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, roots = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            '{} tag does not require an additional argument.'.format(token.split_contents()[0])
        )

    nodes = parser.parse(('end_navbar_blog_categories',))
    parser.delete_first_token()

    return CategoryNode(nodes, roots)


@register.simple_tag
def get_blog_category_roots(blog_slug):
    cache_key = 'blog.templatetags.blog_tags.get_blog_category_roots({})'.format(blog_slug)
    cache_time = settings.CACHES['default']['TIMEOUT']

    roots = cache.get(cache_key)

    if not roots:
        try:
            roots = get_cached_trees(Category.objects
                                     .filter(blog__slug=blog_slug)
                                     .order_by('tree_id', 'lft'))
            cache.set(cache_key, roots, cache_time)
        except Category.DoesNotExist:
            roots = None

    return roots


@register.tag
def blog_categories(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, obj = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            '{} tag does not require an additional argument.'.format(token.split_contents()[0])
        )

    nodes = parser.parse(('end_blog_categories',))
    parser.delete_first_token()

    return CategoryNode(nodes, obj)


@register.simple_tag
def get_recent_posts(blog_slug, count=5):
    cache_key = 'blog.templatetags.blog_tags.get_recent_posts({})'.format(blog_slug)
    cache_time = settings.CACHES['default']['TIMEOUT']

    posts = cache.get(cache_key)

    if not posts:
        posts = Post.objects \
                    .select_related('blog') \
                    .blog(blog_slug) \
                    .published() \
                    .order_by('-published')[:count]
        cache.set(cache_key, posts, cache_time)

    return posts


@register.simple_tag
def get_most_common_tags(blog_slug, min=1, count=10):
    cache_key = 'blog.templatetags.blog_tags.get_most_common_tags({})'.format(blog_slug)
    cache_time = settings.CACHES['default']['TIMEOUT']

    extra_filters = {
        'post__blog__slug': blog_slug,
        'post__status': Post.STATUS_CHOICES.published,
        'post__is_removed': False,
    }

    tags = cache.get(cache_key)

    if not tags:
        tags = Post.tags.most_common(min, extra_filters)[:count]
        cache.set(cache_key, tags, cache_time)

    return tags


@register.simple_tag
def get_similar_posts(post, blog_slug, count=4):
    cache_key = 'blog.templatetags.blog_tags.get_similar_posts({})'.format(blog_slug)
    cache_time = settings.CACHES['default']['TIMEOUT']

    posts = cache.get(cache_key)

    if not posts:
        posts = Post.objects.published() \
                    .filter(tags__in=post.tags.values_list('id', flat=True)) \
                    .exclude(id=post.id) \
                    .annotate(same_tags=Count('tags')) \
                    .order_by('-same_tags', '-published')[:count]
        cache.set(cache_key, posts, cache_time)

    return posts
