from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils import models as model_utils_models


class AbstractSlip(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    STATUS_CHOICES = Choices(
        (0, 'pending', _('transaction pending')),
        (1, 'complete', _('transaction complete')),
        (2, 'revoked', _('transaction revoked')),
    )

    status = models.IntegerField(
        verbose_name=_('slip status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.pending,
        db_index=True,
    )

    amount = models.DecimalField(
        verbose_name=_('transaction amount'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
        default='',
    )

    remarks = models.TextField(
        verbose_name=_('slip remarks'),
        blank=True,
    )

    class Meta:
        abstract = True


class Account(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    TYPE_CHOICES = Choices(
        (0, 'bank_account', _('bank account')),
        (1, 'credit card', _('credit card')),
        (2, 'debit card', _('debit card')),
    )

    type = models.IntegerField(
        verbose_name=_('account type'),
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES.bank_account,
        db_index=True,
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
    )

    active = models.BooleanField(
        verbose_name=_('account active'),
        default=True,
    )

    class Meta:
        verbose_name = _('bookkeeping account')
        verbose_name_plural = _('bookkeeping accounts')

    def __str__(self):
        return '{}'.format(self.title)


class WithdrawalSlip(AbstractSlip):
    TYPE_CHOICES = Choices(
        (0, 'purchase', _('purchase')),
        (1, 'refund', _('refund')),
        (2, 'refund_overdrawn', _('refund overdrawn')),
        (3, 'expense', _('expense')),
        (4, 'salary', _('salary')),
    )

    type = models.IntegerField(
        verbose_name=_('withdrawal type'),
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES.purchase,
        db_index=True,
    )

    account = models.ForeignKey(
        'bookkeeping.Account',
        verbose_name=_('account'),
        db_index=True,
        on_delete=models.CASCADE,
        related_name="withdrawals",
    )

    completed = models.DateTimeField(
        verbose_name=_('completed date'),
        null=True,
    )

    class Meta:
        verbose_name = _('withdrawal slip')
        verbose_name_plural = _('withdrawal slips')

    def __str__(self):
        return 'withdrawal - {} {}'.format(self.type, self.completed)


class UnidentifiedDepositSlip(AbstractSlip):
    TYPE_CHOICES = Choices(
        (0, 'unidentified', _('unidentified')),
        (1, 'identified', _('identified')),
        (2, 'overdrawn', _('overdrawn deposit')),
    )

    type = models.IntegerField(
        verbose_name=_('deposit type'),
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES.unidentified,
        db_index=True,
    )

    account = models.ForeignKey(
        'bookkeeping.Account',
        verbose_name=_('account'),
        db_index=True,
        on_delete=models.CASCADE,
        related_name="unidentified_deposits",
    )

    completed = models.DateTimeField(
        verbose_name=_('completed date'),
        null=True,
    )

    class Meta:
        verbose_name = _('unidentified deposit slip')
        verbose_name_plural = _('unidentified deposit slips')

    def __str__(self):
        return 'deposit - {} {}'.format(self.type, self.completed)
