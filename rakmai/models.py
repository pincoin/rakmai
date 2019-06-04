import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class MenuItem(MPTTModel):
    MATCH_CHOICES = Choices(
        (0, 'equals', _('equals')),
        (1, 'startswith', _('startswith')),
    )

    TARGET_CHOICES = Choices(
        (0, 'self', _('_self')),
        (1, 'blank', _('blank')),
    )

    parent = TreeForeignKey(
        'self',
        verbose_name=_('parent'),
        blank=True,
        null=True,
        related_name='children',
        db_index=True,
        on_delete=models.SET_NULL,
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
        help_text=_('Site menu item title. Can contain template variables E.g.: {{ mytitle }}'),
    )

    url = models.CharField(
        verbose_name=_('url'),
        max_length=255,
        db_index=True,
        help_text=_('Exact URL or URL pattern'),
    )

    match = models.IntegerField(
        verbose_name=_('match'),
        choices=MATCH_CHOICES,
        default=MATCH_CHOICES.equals,
    )

    target = models.IntegerField(
        verbose_name=_('target'),
        choices=TARGET_CHOICES,
        default=TARGET_CHOICES.self,
    )

    class Meta:
        verbose_name = _('menu item')
        verbose_name_plural = _('menu items')

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title


class AbstractPage(TimeStampedModel):
    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
        help_text=_("The page title as you'd like it to be seen by the public"),
    )

    description = models.CharField(
        verbose_name=_('description'),
        max_length=255,
        help_text=_("A short description not longer than 155 characters. Don't use double quotes."),
        blank=True,
    )

    keywords = models.CharField(
        verbose_name=_('keywords'),
        max_length=255,
        help_text=_("A comma-separated list of keywords. Don't use double quotes."),
        blank=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('owner'),
        null=True,
        blank=True,
        editable=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_owned",
    )

    class Meta:
        abstract = True


class AbstractCategory(TimeStampedModel, MPTTModel):
    parent = TreeForeignKey(
        'self',
        verbose_name=_('parent'),
        blank=True,
        null=True,
        related_name='children',
        db_index=True,
        on_delete=models.SET_NULL,
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=128,
    )

    slug = models.SlugField(
        verbose_name=_('slug'),
        help_text=_('A short label containing only letters, numbers, underscores or hyphens for URL'),
        max_length=255,
        unique=True,
        allow_unicode=True,
    )

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ['created']


class AbstractAttachment(models.Model):
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('file name'),
    )

    # PK is a private identifier
    uid = models.UUIDField(
        verbose_name=_('public identifier'),
        unique=True,
        default=uuid.uuid4,
        editable=False,
    )

    file = models.FileField(
        verbose_name=_('uploaded file'),
        upload_to="attachments",
    )

    created = models.DateTimeField(
        verbose_name=_('created time'),
        auto_now_add=True,
    )

    class Meta:
        abstract = True
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')

    def __str__(self):
        return self.name


class AbstractComment(TimeStampedModel, MPTTModel):
    STATUS_CHOICES = Choices(
        (0, 'approved', _('approved')),
        (1, 'flagged', _('flagged')),
        (2, 'deleted', _('deleted')),
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    parent = TreeForeignKey(
        'self',
        verbose_name=_('parent'),
        blank=True,
        null=True,
        related_name='children',
        db_index=True,
        on_delete=models.SET_NULL,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('owner'),
        null=True,
        blank=True,
        editable=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_owned",
    )

    username = models.CharField(
        verbose_name=_('username'),
        max_length=32,
        null=True,
        blank=True,
    )

    email = models.EmailField(
        verbose_name=_('email address'),
        null=True,
        blank=True,
    )

    url = models.URLField(
        verbose_name=_('website URL'),
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.approved,
        db_index=True,
    )

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ['-created']

    def __str__(self):
        return '{} comment'.format(self.owner)


class Google(TimeStampedModel):
    site_id = models.IntegerField(
        verbose_name=_('site id'),
    )

    analytics_uid = models.CharField(
        verbose_name=_('Google Analytics UA-ID'),
        max_length=128,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('Google Service')
        verbose_name_plural = _('Google Services')
