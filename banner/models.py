import uuid

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from model_utils import Choices
from model_utils.models import (
    TimeStampedModel, TimeFramedModel
)


def upload_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/banner/<today>/<uuid>.<ext>
    return 'banner/{}/{}.{}'.format(now().strftime('%Y-%m-%d'), uuid.uuid4(), filename.split('.')[-1])


class Banner(TimeFramedModel, TimeStampedModel):
    STATUS_CHOICES = Choices(
        (0, 'enabled', _('enabled')),
        (1, 'disabled', _('disabled')),
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=80,
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.enabled,
        db_index=True,
    )

    class Meta:
        verbose_name = _('banner')
        verbose_name_plural = _('banners')

    def __str__(self):
        return self.title


class BannerItem(TimeStampedModel):
    TARGET_CHOICES = Choices(
        (0, 'self', _('_self')),
        (1, 'blank', _('blank')),
    )

    STATUS_CHOICES = Choices(
        (0, 'visible', _('visible')),
        (1, 'hidden', _('hidden')),
    )

    banner = models.ForeignKey(
        'banner.Banner',
        verbose_name=_('banner'),
        blank=True,
        null=True,
        related_name='banners',
        db_index=True,
        on_delete=models.SET_NULL,
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=80,
    )

    url = models.URLField(
        verbose_name=_('url'),
    )

    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
        null=True,
    )

    target = models.IntegerField(
        verbose_name=_('target'),
        choices=TARGET_CHOICES,
        default=TARGET_CHOICES.self,
    )

    position = models.IntegerField(
        verbose_name=_('position'),
        default=0,
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.visible,
        db_index=True,
    )

    thumbnail = ThumbnailerImageField(
        verbose_name=_('thumbnail'),
        upload_to=upload_directory_path,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('banner item')
        verbose_name_plural = _('banner items')

    def __str__(self):
        return self.title
