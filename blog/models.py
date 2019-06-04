import uuid

from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse
from django.utils.text import slugify as default_slugify
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from model_utils import Choices
from model_utils.models import (
    TimeStampedModel, SoftDeletableModel
)
from mptt.fields import TreeForeignKey
from taggit.managers import TaggableManager
from taggit.models import (
    TagBase, TaggedItemBase
)

from rakmai.models import (
    AbstractPage, AbstractCategory, AbstractAttachment, AbstractComment
)
from .managers import PostManager


def upload_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/blog/<today>/<uuid>.<ext>
    return 'blog/{}/{}.{}'.format(now().strftime('%Y-%m-%d'), uuid.uuid4(), filename.split('.')[-1])


class Blog(TimeStampedModel):
    FORMAT_CHOICES = Choices(
        (0, 'html', _('html')),
        (1, 'markdown', _('markdown')),
        (2, 'text', _('text')),
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=250,
    )

    slug = models.SlugField(
        verbose_name=_('slug'),
        help_text=_('A short label containing only letters, numbers, underscores or hyphens for URL'),
        max_length=255,
        unique=True,
        allow_unicode=True,
    )

    theme = models.CharField(
        verbose_name=_('theme'),
        max_length=250,
        default='default',
    )

    markup = models.IntegerField(
        verbose_name=_('markup'),
        choices=FORMAT_CHOICES,
        default=FORMAT_CHOICES.html,
    )

    allow_comments = models.BooleanField(
        verbose_name=_('allow comments'),
        default=True,
    )

    chunk_size = models.PositiveIntegerField(
        verbose_name=_('pagination chunk size'),
        default=10,
    )

    block_size = models.PositiveIntegerField(
        verbose_name=_('pagination block size'),
        default=10,
    )

    rss_size = models.PositiveIntegerField(
        verbose_name=_('RSS size'),
        default=10,
    )

    class Meta:
        verbose_name = _('blog')
        verbose_name_plural = _('blogs')

    def __str__(self):
        return self.title


class Attachment(AbstractAttachment):
    file = models.FileField(
        verbose_name=_('uploaded file'),
        upload_to=upload_directory_path,
        storage=default_storage,
    )

    post = models.ForeignKey(
        'blog.Post',
        verbose_name=_('post'),
        related_name='attachments',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')


class PostTag(TagBase):
    # NOTE: django-taggit does not allow unicode by default.
    slug = models.SlugField(
        verbose_name=_('slug'),
        unique=True,
        max_length=100,
        allow_unicode=True,
    )

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def slugify(self, tag, i=None):
        return default_slugify(tag, allow_unicode=True)


class TaggedPost(TaggedItemBase):
    content_object = models.ForeignKey(
        'blog.Post',
        on_delete=models.CASCADE,
    )

    tag = models.ForeignKey(
        'blog.PostTag',
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("tagged post")
        verbose_name_plural = _("tagged posts")


class Category(AbstractCategory):
    blog = models.ForeignKey(
        'blog.Blog',
        verbose_name=_('blog'),
        related_name='categories',
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.title


class Post(SoftDeletableModel, AbstractPage):
    STATUS_CHOICES = Choices(
        (0, 'draft', _('draft')),
        (1, 'published', _('published')),
        (2, 'hidden', _('hidden')),
    )

    blog = models.ForeignKey(
        'blog.Blog',
        verbose_name=_('blog'),
        related_name='posts',
        on_delete=models.CASCADE,
    )

    slug = models.SlugField(
        verbose_name=_('slug'),
        help_text=_('A short label containing only letters, numbers, underscores or hyphens for URL'),
        max_length=255,
        # unique=True,
        allow_unicode=True,
    )

    excerpt = models.TextField(
        verbose_name=_('excerpt'),
        help_text=_('A short description which does not contain HTML tags'),
        blank=True,
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    category = TreeForeignKey(
        'blog.Category',
        verbose_name=_('category'),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )

    tags = TaggableManager(
        verbose_name=_('tags'),
        help_text=_('A comma-separated list of tags.'),
        blank=True,
        through=TaggedPost,
    )

    thumbnail = ThumbnailerImageField(
        verbose_name=_('thumbnail'),
        upload_to=upload_directory_path,
        blank=True,
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.draft,
        db_index=True,
    )

    allow_highlight = models.BooleanField(
        verbose_name=_('allow code highlighting'),
        default=False,
    )

    allow_comments = models.BooleanField(
        verbose_name=_('allow comments'),
        default=True,
    )

    published = models.DateTimeField(
        verbose_name=_('published date'),
        null=True,
    )

    view_count = models.PositiveIntegerField(
        verbose_name=_('view count'),
        default=0,
    )

    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
    )

    objects = PostManager()

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')

    def __str__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.old_status = self.status
        self.old_published = self.published

    def save(self, *args, **kwargs):
        if self.old_status != self.status \
                and self.status == Post.STATUS_CHOICES.published \
                and self.old_published is None:
            self.published = now()

        super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post-detail', args=[self.blog.slug, self.pk, self.slug])

    def get_previous_post(self):
        previous_post = Post.objects.published().filter(id__lt=self.id).order_by('-published').first()

        if previous_post is None:
            return None

        return reverse('blog:post-detail', args=[self.blog.slug, previous_post.pk, previous_post.slug])

    def get_next_post(self):
        next_post = Post.objects.published().filter(id__gt=self.id).order_by('-published').last()

        if next_post is None:
            return None

        return reverse('blog:post-detail', args=[self.blog.slug, next_post.pk, next_post.slug])


class Comment(SoftDeletableModel, AbstractComment):
    post = models.ForeignKey(
        'blog.Post',
        verbose_name=_('post'),
        related_name='comments',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
