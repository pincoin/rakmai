import uuid

from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.models import (
    TimeStampedModel, SoftDeletableModel
)
from mptt.fields import TreeForeignKey

from rakmai.models import AbstractAttachment
from rakmai.models import (
    AbstractPage, AbstractCategory
)
from .managers import MessageManager


def upload_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/board/<today>/<uuid>.<ext>
    return 'board/{}/{}.{}'.format(now().strftime('%Y-%m-%d'), uuid.uuid4(), filename.split('.')[-1])


class Board(TimeStampedModel):
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

    allow_comments = models.BooleanField(
        verbose_name=_('allow comments'),
        default=True,
    )

    chunk_size = models.PositiveIntegerField(
        verbose_name=_('pagination chunk size'),
        default=20,
    )

    block_size = models.PositiveIntegerField(
        verbose_name=_('pagination block size'),
        default=10,
    )

    class Meta:
        verbose_name = _('board')
        verbose_name_plural = _('boards')

    def __str__(self):
        return self.title


class Category(AbstractCategory):
    board = models.ForeignKey(
        'board.Board',
        verbose_name=_('category'),
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


class Attachment(AbstractAttachment):
    file = models.FileField(
        verbose_name=_('uploaded file'),
        upload_to=upload_directory_path,
        storage=default_storage,
    )

    message = models.ForeignKey(
        'board.Message',
        verbose_name=_('message'),
        related_name='attachments',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')


class Message(SoftDeletableModel, AbstractPage):
    STATUS_CHOICES = Choices(
        (0, 'published', _('published')),
        (1, 'moderated', _('moderated')),
    )

    FORMAT_CHOICES = Choices(
        (0, 'html', _('html')),
        (1, 'markdown', _('markdown')),
        (2, 'text', _('text')),
    )

    board = models.ForeignKey(
        'board.Board',
        verbose_name=_('board'),
        related_name='messages',
        on_delete=models.CASCADE,
    )

    nickname = models.CharField(
        verbose_name=_('nickname'),
        max_length=30,
        blank=True
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    category = TreeForeignKey(
        'board.Category',
        verbose_name=_('category'),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.published,
        db_index=True,
    )

    secret = models.BooleanField(
        verbose_name=_('secret'),
        default=False,
    )

    sticky = models.BooleanField(
        verbose_name=_('sticky'),
        default=False,
    )

    markup = models.IntegerField(
        verbose_name=_('markup'),
        choices=FORMAT_CHOICES,
        default=FORMAT_CHOICES.html,
    )

    view_count = models.PositiveIntegerField(
        verbose_name=_('view count'),
        default=0,
    )

    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
    )

    objects = MessageManager()

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('board:message-detail', args=[self.slug, self.pk])
