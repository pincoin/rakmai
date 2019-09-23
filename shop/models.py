import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from model_utils import Choices
from model_utils import models as model_utils_models
from model_utils.fields import StatusField
from mptt.fields import TreeForeignKey

from rakmai import models as rakmai_models
from . import managers


def upload_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/blog/<today>/<uuid>.<ext>
    return 'shop/{}/{}.{}'.format(now().strftime('%Y-%m-%d'), uuid.uuid4(), filename.split('.')[-1])


class Store(model_utils_models.TimeStampedModel):
    STATUS_CHOICES = Choices(
        (0, 'enabled', _('enabled')),
        (1, 'disabled', _('disabled')),
        (2, 'maintenance', _('maintenance'))
    )

    name = models.CharField(
        verbose_name=_('store name'),
        max_length=255,
    )

    code = models.SlugField(
        verbose_name=_('store code'),
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

    phone = models.CharField(
        verbose_name=_('phone number'),
        max_length=16,
        blank=True,
        null=True,
    )

    phone1 = models.CharField(
        verbose_name=_('phone number1'),
        max_length=16,
        blank=True,
        null=True,
    )

    kakao = models.CharField(
        verbose_name=_('kakao ID'),
        max_length=16,
        blank=True,
        null=True,
    )

    bank_account = models.TextField(
        verbose_name=_('bank accounts'),
        blank=True,
    )

    escrow_account = models.TextField(
        verbose_name=_('escrow'),
        blank=True,
    )

    chunk_size = models.PositiveIntegerField(
        verbose_name=_('pagination chunk size'),
        default=10,
    )

    block_size = models.PositiveIntegerField(
        verbose_name=_('pagination block size'),
        default=10,
    )

    class Meta:
        verbose_name = _('store')
        verbose_name_plural = _('stores')

    def __str__(self):
        return self.name


class Category(rakmai_models.AbstractCategory):
    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        related_name='categories',
        db_index=True,
        on_delete=models.CASCADE,
    )

    thumbnail = ThumbnailerImageField(
        verbose_name=_('thumbnail'),
        upload_to=upload_directory_path,
        blank=True,
    )

    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
    )

    description1 = models.TextField(
        verbose_name=_('description1'),
        blank=True,
    )

    discount_rate = models.DecimalField(
        verbose_name=_('discount rate'),
        max_digits=3,
        decimal_places=2,
    )

    pg = models.BooleanField(
        verbose_name=_('Payment Gateway'),
        default=False,
    )

    pg_discount_rate = models.DecimalField(
        verbose_name=_('PG discount rate'),
        max_digits=3,
        decimal_places=2,
        default=0,
    )

    naver_search_tag = models.CharField(
        verbose_name=_('Naver Search Tag'),
        max_length=99,
        blank=True,
    )

    naver_brand_name = models.CharField(
        verbose_name=_('Naver Brand Name'),
        max_length=59,
        blank=True,
    )

    naver_maker_name = models.CharField(
        verbose_name=_('Naver Maker Name'),
        max_length=59,
        blank=True,
    )

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.title


class Product(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    STATUS_CHOICES = Choices(
        (0, 'enabled', _('enabled')),
        (1, 'disabled', _('disabled')),
    )

    STOCK_CHOICES = Choices(
        (0, 'sold_out', _('sold out')),
        (1, 'in_stock', _('in stock')),
    )

    name = models.CharField(
        verbose_name=_('product name'),
        max_length=255,
    )

    subtitle = models.CharField(
        verbose_name=_('product subtitle'),
        max_length=255,
        blank=True,
    )

    code = models.SlugField(
        verbose_name=_('product code'),
        help_text=_('A short label containing only letters, numbers, underscores or hyphens for URL'),
        max_length=255,
        unique=True,
        allow_unicode=True,
    )

    # Max = 999,999,999.99
    list_price = models.DecimalField(
        verbose_name=_('list price'),
        max_digits=11,
        decimal_places=2,
    )

    selling_price = models.DecimalField(
        verbose_name=_('selling price'),
        max_digits=11,
        decimal_places=2,
    )

    pg = models.BooleanField(
        verbose_name=_('Payment Gateway'),
        default=False,
    )

    pg_selling_price = models.DecimalField(
        verbose_name=_('Payment Gateway selling price'),
        max_digits=11,
        decimal_places=2,
        default=0,
    )

    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
    )

    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        db_index=True,
        on_delete=models.CASCADE,
    )

    category = TreeForeignKey(
        'shop.Category',
        verbose_name=_('category'),
        db_index=True,
        on_delete=models.CASCADE,
    )

    position = models.IntegerField(
        verbose_name=_('position'),
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.disabled,
        db_index=True,
    )

    stock = models.IntegerField(
        verbose_name=_('stock'),
        choices=STOCK_CHOICES,
        default=STOCK_CHOICES.in_stock,
        db_index=True,
    )

    minimum_stock_level = models.IntegerField(
        verbose_name=_('minimum stock level'),
        default=0,
    )

    maximum_stock_level = models.IntegerField(
        verbose_name=_('maximum stock level'),
        default=0,
    )

    review_count = models.PositiveIntegerField(
        verbose_name=_('review comment count'),
        default=0,
    )

    review_count_pg = models.PositiveIntegerField(
        verbose_name=_('review comment count(PG)'),
        default=0,
    )

    naver_partner = models.BooleanField(
        verbose_name=_('Naver Shopping Partner Zone Status'),
        default=False,
    )

    naver_partner_title = models.CharField(
        verbose_name=_('Naver Shopping Partner Zone Product Name'),
        max_length=255,
        blank=True,
    )

    naver_partner_title_pg = models.CharField(
        verbose_name=_('Naver Shopping Partner Zone Product Name (PG)'),
        max_length=255,
        blank=True,
    )

    naver_attribute = models.CharField(
        verbose_name=_('Naver Attributes'),
        max_length=499,
        blank=True,
    )

    objects = managers.ProductManager()

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        return '{} {}'.format(self.name, self.subtitle)

    @property
    def discount_rate(self):
        if self.list_price and self.selling_price:
            return (self.list_price - self.selling_price) * 100 / self.list_price
        return 0.0

    @property
    def pg_discount_rate(self):
        if self.list_price and self.pg_selling_price:
            return (self.list_price - self.pg_selling_price) * 100 / self.list_price
        return 0.0

    def get_absolute_url(self):
        return reverse('shop:product-detail', args=[self.store.code, self.pk, self.code])


class ProductList(model_utils_models.TimeStampedModel):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=255,
    )

    code = models.CharField(
        verbose_name=_('code'),
        max_length=255,
    )

    products = models.ManyToManyField(Product, through='ProductListMembership')

    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        db_index=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('product list')
        verbose_name_plural = _('product lists')

    def __str__(self):
        return self.name


class ProductListMembership(models.Model):
    product = models.ForeignKey(
        'shop.Product',
        verbose_name=_('product'),
        db_index=True,
        on_delete=models.CASCADE,
    )

    product_list = models.ForeignKey(
        'shop.ProductList',
        verbose_name=_('product list'),
        db_index=True,
        on_delete=models.CASCADE,
    )

    position = models.IntegerField(
        verbose_name=_('position'),
    )

    class Meta:
        verbose_name = _('product list membership')
        verbose_name_plural = _('product list membership')


class Order(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    PAYMENT_METHOD_CHOICES = Choices(
        (0, 'bank_transfer', _('Bank Transfer')),
        (1, 'escrow', _('Escrow (KB)')),
        (2, 'paypal', _('PayPal')),
        (3, 'credit_card', _('Credit Card')),
        (4, 'bank_transfer_pg', _('Bank Transfer (PG)')),
        (5, 'virtual_account', _('Virtual Account')),
    )

    # TODO: order status != payment status
    # 전액환불요청 (total refund requested)
    # 부분환불요청 (partial refund requested)
    # 전액환불됨 (total refund)
    # 부분환불됨 (partial refund)
    STATUS_CHOICES = Choices(
        (0, 'payment_pending', _('payment pending')),
        (1, 'payment_completed', _('payment completed')),
        (2, 'under_review', _('under review')),
        (3, 'payment_verified', _('payment verified')),
        (4, 'shipped', _('shipped')),
        (5, 'refund_requested', _('refund requested')),
        (6, 'refund_pending', _('refund pending')),
        (7, 'refunded1', _('refunded')),  # original order
        (8, 'refunded2', _('refunded')),  # refund order
        (9, 'voided', _('voided')),
    )

    VISIBLE_CHOICES = Choices(
        (0, 'hidden', _('Hidden')),
        (1, 'visible', _('Visible')),
    )

    CURRENCY_CHOICES = Choices('KRW', 'USD')

    order_no = models.UUIDField(
        verbose_name=_('order no'),
        unique=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        db_index=True,
        null=True,
        blank=True,
        editable=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_owned",
    )

    fullname = models.CharField(
        verbose_name=_('fullname'),
        max_length=64,
        blank=True,
    )

    user_agent = models.TextField(
        verbose_name=_('user-agent'),
        blank=True,
    )

    accept_language = models.TextField(
        verbose_name=_('accept-language'),
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
    )

    payment_method = models.IntegerField(
        verbose_name=_('payment method'),
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_CHOICES.bank_transfer,
        db_index=True,
    )

    transaction_id = models.CharField(
        verbose_name=_('transaction id'),
        max_length=64,
        blank=True,
    )

    status = models.IntegerField(
        verbose_name=_('order status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.payment_pending,
        db_index=True,
    )

    visible = models.IntegerField(
        verbose_name=_('visible status'),
        choices=VISIBLE_CHOICES,
        default=VISIBLE_CHOICES.visible,
        db_index=True,
    )

    # Max = 999,999,999.99
    total_list_price = models.DecimalField(
        verbose_name=_('total list price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    total_selling_price = models.DecimalField(
        verbose_name=_('total price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    currency = StatusField(
        verbose_name=_('currency'),
        choices_name='CURRENCY_CHOICES',
    )

    message = models.TextField(
        verbose_name=_('order message'),
        blank=True,
    )

    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent'),
        related_name='children',
        db_index=True,
        null=True,
        on_delete=models.CASCADE,
    )

    suspicious = models.BooleanField(
        verbose_name=_('suspicious'),
        default=False,
    )

    objects = managers.OrderManager()

    class Meta:
        verbose_name = _('pincoin order')
        verbose_name_plural = _('pincoin orders')

    def __str__(self):
        return '{} {} {}'.format(self.user, self.total_selling_price, self.created)


class OrderPayment(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    ACCOUNT_CHOICES = Choices(
        (0, 'kb', _('KOOKMIN BANK')),
        (1, 'nh', _('NONGHYUP BANK')),
        (2, 'shinhan', _('SHINHAN BANK')),
        (3, 'woori', _('WOORI BANK')),
        (4, 'ibk', _('IBK BANK')),
        (5, 'paypal', _('PayPal')),
    )

    order = models.ForeignKey(
        'shop.Order',
        verbose_name=_('order'),
        related_name='payments',
        db_index=True,
        on_delete=models.CASCADE,
    )

    account = models.IntegerField(
        verbose_name=_('account'),
        choices=ACCOUNT_CHOICES,
        default=ACCOUNT_CHOICES.kb,
        db_index=True,
    )

    amount = models.DecimalField(
        verbose_name=_('amount'),
        max_digits=11,
        decimal_places=2,
    )

    received = models.DateTimeField(
        verbose_name=_('received date'),
    )

    class Meta:
        verbose_name = _('order payment')
        verbose_name_plural = _('order payments')

    def __str__(self):
        return 'order - {} / payment - {} {} {}'.format(
            self.order.order_no, self.account, self.amount, self.received
        )


class OrderProduct(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    order = models.ForeignKey(
        'shop.Order',
        verbose_name=_('order'),
        related_name='products',
        db_index=True,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        verbose_name=_('product name'),
        max_length=255,
    )

    subtitle = models.CharField(
        verbose_name=_('product subtitle'),
        max_length=255,
        blank=True,
    )

    code = models.CharField(
        verbose_name=_('product code'),
        max_length=255,
    )

    # Max = 999,999,999.99
    list_price = models.DecimalField(
        verbose_name=_('list price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    selling_price = models.DecimalField(
        verbose_name=_('selling price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    quantity = models.IntegerField(
        verbose_name=_('quantity'),
        default=0,
    )

    @property
    def subtotal(self):
        return self.selling_price * self.quantity

    class Meta:
        verbose_name = _('order product')
        verbose_name_plural = _('order products')

    def __str__(self):
        return 'order - {} / product - {}'.format(self.order.order_no, self.name)


class OrderProductVoucher(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    order_product = models.ForeignKey(
        'shop.OrderProduct',
        verbose_name=_('order product'),
        related_name='codes',
        db_index=True,
        on_delete=models.CASCADE,
    )

    voucher = models.ForeignKey(
        'shop.Voucher',
        verbose_name=_('voucher'),
        related_name='vouchers_sold',
        db_index=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    code = models.CharField(
        verbose_name=_('voucher code'),
        max_length=64,
    )

    revoked = models.BooleanField(
        verbose_name=_('revoked'),
        default=False,
    )

    remarks = models.CharField(
        verbose_name=_('voucher remarks'),
        max_length=64,
        blank=True,
    )

    class Meta:
        verbose_name = _('order voucher code')
        verbose_name_plural = _('order voucher codes')

    def __str__(self):
        return '{} ({}-{})'.format(self.order_product.name, self.code, self.remarks)


class Voucher(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    STATUS_CHOICES = Choices(
        (0, 'purchased', _('purchased')),
        (1, 'sold', _('sold')),
        (2, 'revoked', _('revoked')),
    )

    product = models.ForeignKey(
        'shop.Product',
        verbose_name=_('product'),
        related_name='vouchers',
        db_index=True,
        on_delete=models.PROTECT,
    )

    code = models.CharField(
        verbose_name=_('voucher code'),
        max_length=64,
    )

    remarks = models.CharField(
        verbose_name=_('voucher remarks'),
        max_length=64,
        blank=True,
    )

    status = models.IntegerField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.purchased,
        db_index=True,
    )

    class Meta:
        verbose_name = _('voucher')
        verbose_name_plural = _('vouchers')

        unique_together = ('product', 'code',)

        indexes = [
            models.Index(fields=['code', ]),
        ]

    def __str__(self):
        return '{}'.format(self.code)


class NoticeMessage(model_utils_models.SoftDeletableModel, rakmai_models.AbstractPage):
    CATEGORY_CHOICES = Choices(
        (0, 'common', _('Common')),
        (1, 'event', _('Game Event')),
        (2, 'price', _('Price Policy')),
    )

    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        related_name='notice_messages',
        on_delete=models.CASCADE,
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    category = models.IntegerField(
        verbose_name=_('category'),
        choices=CATEGORY_CHOICES,
        default=CATEGORY_CHOICES.common,
        db_index=True,
    )

    class Meta:
        verbose_name = _('notice')
        verbose_name_plural = _('notice')

    def __str__(self):
        return self.title


class FaqMessage(model_utils_models.SoftDeletableModel, rakmai_models.AbstractPage):
    CATEGORY_CHOICES = Choices(
        (0, 'registration', _('Registration')),
        (1, 'verification', _('Verification')),
        (2, 'order', _('Order/Stock')),
        (3, 'payment', _('Payment')),
        (4, 'delivery', _('Delivery')),
    )

    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        related_name='faq_messages',
        on_delete=models.CASCADE,
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    category = models.IntegerField(
        verbose_name=_('category'),
        choices=CATEGORY_CHOICES,
        default=CATEGORY_CHOICES.registration,
        db_index=True,
    )

    position = models.IntegerField(
        verbose_name=_('position'),
    )

    class Meta:
        verbose_name = _('frequently asked question')
        verbose_name_plural = _('frequently asked questions')

    def __str__(self):
        return self.title


class CustomerQuestion(model_utils_models.SoftDeletableModel, rakmai_models.AbstractPage):
    CATEGORY_CHOICES = Choices(
        (0, 'registration', _('Registration')),
        (1, 'verification', _('Verification')),
        (2, 'order', _('Order/Stock')),
        (3, 'payment', _('Payment')),
        (4, 'delivery', _('Late Delivery')),
    )

    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        related_name='customer_questions',
        on_delete=models.CASCADE,
    )

    order = models.ForeignKey(
        'shop.Order',
        verbose_name=_('order'),
        related_name='questions',
        db_index=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    category = models.IntegerField(
        verbose_name=_('category'),
        choices=CATEGORY_CHOICES,
        default=CATEGORY_CHOICES.registration,
        db_index=True,
    )

    class Meta:
        verbose_name = _('customer question')
        verbose_name_plural = _('customer questions')

    def __str__(self):
        return self.title


class QuestionAnswer(model_utils_models.TimeStampedModel):
    content = models.TextField(
        verbose_name=_('content'),
    )

    question = models.ForeignKey(
        'shop.CustomerQuestion',
        verbose_name=_('question'),
        related_name='answers',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('question answer')
        verbose_name_plural = _('question answers')


class Testimonials(model_utils_models.SoftDeletableModel, rakmai_models.AbstractPage):
    store = models.ForeignKey(
        'shop.Store',
        verbose_name=_('store'),
        related_name='testimonials',
        on_delete=models.CASCADE,
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    class Meta:
        verbose_name = _('testimonials')
        verbose_name_plural = _('testimonials')

    def __str__(self):
        return self.title


class TestimonialsAnswer(model_utils_models.TimeStampedModel):
    content = models.TextField(
        verbose_name=_('content'),
    )

    testimonial = models.ForeignKey(
        'shop.Testimonials',
        verbose_name=_('testimonials'),
        related_name='answers',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('testimonials answer')
        verbose_name_plural = _('testimonials answers')


class ShortMessageService(model_utils_models.TimeStampedModel):
    phone_from = models.CharField(
        verbose_name=_('from phone number'),
        max_length=16,
        blank=True,
        null=True,
    )

    phone_to = models.CharField(
        verbose_name=_('to phone number'),
        max_length=16,
        blank=True,
        null=True,
    )

    content = models.TextField(
        verbose_name=_('content'),
    )

    success = models.BooleanField(
        verbose_name=_('success'),
        default=True,
    )

    class Meta:
        verbose_name = _('short message')
        verbose_name_plural = _('short messages')

    def __str__(self):
        return '{} {} {}'.format(self.phone_from, self.phone_to, self.created)


class LegacyCustomer(models.Model):
    customer_id = models.IntegerField(
        verbose_name=_('customer id'),
        unique=True,
    )

    email = models.CharField(
        verbose_name=_('email'),
        max_length=254,
    )

    last_name = models.CharField(
        verbose_name=_('last name'),
        max_length=32,
    )

    first_name = models.CharField(
        verbose_name=_('first name'),
        max_length=32,
    )

    date_joined = models.DateTimeField(
        verbose_name=_('date joined'),
        blank=True,
    )

    phone = models.CharField(
        verbose_name=_('phone number'),
        max_length=16,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('legacy customer')
        verbose_name_plural = _('legacy customers')

    def __str__(self):
        return '{} {}'.format(self.customer_id, self.phone)


class LegacyOrder(models.Model):
    customer_id = models.OneToOneField(
        'shop.LegacyCustomer',
        verbose_name=_('customer id'),
        to_field='customer_id',
        related_name='order',
        db_index=True,
        on_delete=models.CASCADE,
    )

    last_purchased = models.DateTimeField(
        verbose_name=_('last purchased date'),
        blank=True,
    )

    total_order_count = models.IntegerField(
        verbose_name=_('total order count'),
        default=0,
    )

    last_total = models.DecimalField(
        verbose_name=_('last total'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    max_price = models.DecimalField(
        verbose_name=_('max price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    average_price = models.DecimalField(
        verbose_name=_('average price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    class Meta:
        verbose_name = _('legacy order')
        verbose_name_plural = _('legacy orders')

    def __str__(self):
        return '{} {} {}'.format(self.customer_id, self.last_purchased, self.total_order_count)


class LegacyOrderProduct(models.Model):
    customer_id = models.ForeignKey(
        'shop.LegacyCustomer',
        verbose_name=_('customer id'),
        to_field='customer_id',
        related_name='products',
        db_index=True,
        on_delete=models.CASCADE,
    )

    product_name = models.CharField(
        verbose_name=_('product name'),
        max_length=128,
    )

    class Meta:
        verbose_name = _('legacy order product')
        verbose_name_plural = _('legacy order products')

    def __str__(self):
        return '{} {}'.format(self.customer_id, self.product_name)


class NaverOrder(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    PAYMENT_METHOD_CHOICES = Choices(
        (0, 'bank_transfer', _('Bank Transfer')),
    )

    # TODO: order status != payment status
    STATUS_CHOICES = Choices(
        (0, 'payment_pending', _('payment pending')),
        (1, 'payment_completed', _('payment completed')),
        (2, 'under_review', _('under review')),
        (3, 'payment_verified', _('payment verified')),
        (4, 'shipped', _('shipped')),
        (5, 'refund_requested', _('refund requested')),
        (6, 'refund_pending', _('refund pending')),
        (7, 'refunded', _('refunded')),  # original order
        (8, 'voided', _('voided')),
    )

    order_no = models.UUIDField(
        verbose_name=_('order no'),
        unique=True,
        default=uuid.uuid4,
        editable=False
    )

    fullname = models.CharField(
        verbose_name=_('fullname'),
        max_length=64,
    )

    phone = models.CharField(
        verbose_name=_('phone number'),
        max_length=16,
    )

    payment_method = models.IntegerField(
        verbose_name=_('payment method'),
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_CHOICES.bank_transfer,
        db_index=True,
    )

    transaction_id = models.CharField(
        verbose_name=_('transaction id'),
        max_length=64,
        blank=True,
    )

    status = models.IntegerField(
        verbose_name=_('order status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.payment_verified,
        db_index=True,
    )

    # Max = 999,999,999.99
    total_list_price = models.DecimalField(
        verbose_name=_('total list price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    total_selling_price = models.DecimalField(
        verbose_name=_('total price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    message = models.TextField(
        verbose_name=_('order message'),
        blank=True,
    )

    class Meta:
        verbose_name = _('naver order')
        verbose_name_plural = _('naver orders')

    def __str__(self):
        return '{} {} {}'.format(self.fullname, self.total_selling_price, self.created)


class NaverOrderProduct(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    order = models.ForeignKey(
        'shop.NaverOrder',
        verbose_name=_('order'),
        related_name='products',
        db_index=True,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        verbose_name=_('product name'),
        max_length=255,
    )

    subtitle = models.CharField(
        verbose_name=_('product subtitle'),
        max_length=255,
        blank=True,
    )

    code = models.CharField(
        verbose_name=_('product code'),
        max_length=255,
    )

    # Max = 999,999,999.99
    list_price = models.DecimalField(
        verbose_name=_('list price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    selling_price = models.DecimalField(
        verbose_name=_('selling price'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    quantity = models.IntegerField(
        verbose_name=_('quantity'),
        default=0,
    )

    @property
    def subtotal(self):
        return self.selling_price * self.quantity

    class Meta:
        verbose_name = _('naver order product')
        verbose_name_plural = _('naver order products')

    def __str__(self):
        return 'order - {} / product - {}'.format(self.order.order_no, self.name)


class NaverOrderProductVoucher(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    order_product = models.ForeignKey(
        'shop.NaverOrderProduct',
        verbose_name=_('order product'),
        related_name='codes',
        db_index=True,
        on_delete=models.CASCADE,
    )

    voucher = models.ForeignKey(
        'shop.Voucher',
        verbose_name=_('voucher'),
        related_name='naver_vouchers_sold',
        db_index=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    code = models.CharField(
        verbose_name=_('voucher code'),
        max_length=64,
    )

    revoked = models.BooleanField(
        verbose_name=_('revoked'),
        default=False,
    )

    remarks = models.CharField(
        verbose_name=_('voucher remarks'),
        max_length=64,
        blank=True,
    )

    class Meta:
        verbose_name = _('naver order voucher code')
        verbose_name_plural = _('naver order voucher codes')

    def __str__(self):
        return '{} ({}-{})'.format(self.order_product.name, self.code, self.remarks)


class NaverAdvertisementLog(model_utils_models.TimeStampedModel):
    CAMPAIGN_TYPE_CHOICES = Choices(
        (1, 'C1', '파워링크'),
        (2, 'C2', '쇼핑검색'),
        (4, 'C4', '브랜드검색'),
    )

    MEDIA_CHOICES = Choices(
        (27758, 'M27758', '네이버 통합검색 - PC'),
        (8753, 'M8753', '네이버 통합검색 - 모바일'),
        (122876, 'M122876', '네이버 검색탭'),
        (122875, 'M122875', '네이버 통합검색 광고더보기'),
        (11068, 'M11068', '네이버 쇼핑 - PC'),
        (33421, 'M33421', '네이버 쇼핑 - 모바일'),
        (1525, 'M1525', '네이버 지식iN - PC'),
        (36010, 'M36010', '네이버 지식iN - 모바일'),
        (96499, 'M96499', '네이버 카페 - PC'),
        (96500, 'M96500', '네이버 카페 - 모바일'),
        (118495, 'M118495', 'ZUM - PC'),
        (118496, 'M118496', 'ZUM - 모바일'),
        (171229, 'M171229', '네이버 뉴스 - 모바일'),
        (171228, 'M171228', '네이버 뿜 - 모바일'),
        (168243, 'M168243', '네이버 스포츠뉴스 - 모바일'),
        (168242, 'M168242', '네이버 연예뉴스 - 모바일'),
        (171227, 'M171227', '네이버 웹소설 - 모바일'),
        (175890, 'M175890', '네이버 웹툰 - 모바일'),
        (103848, 'M103848', '밴드(BAND) - 모바일'),
        (38367, 'M38367', '11번가 - PC'),
        (38630, 'M38630', '11번가 - 모바일'),
        (37853, 'M37853', '2CPU'),
        (23650, 'M23650', '82cook'),
        (37420, 'M37420', 'AK몰 - PC'),
        (45140, 'M45140', 'AK몰 - 모바일'),
        (11069, 'M11069', 'BB'),
        (1648, 'M1648', 'G마켓'),
        (131017, 'M131017', 'G마켓 - 모바일'),
        (141122, 'M141122', 'SLR클럽'),
        (66998, 'M66998', 'YTN'),
        (67582, 'M67582', 'YTN - 모바일'),
        (23680, 'M23680', 'iMBC'),
        (23093, 'M23093', 'it조선'),
        (81750, 'M81750', '가생이닷컴'),
        (37588, 'M37588', '가자아이'),
        (15121, 'M15121', '간호잡'),
        (58824, 'M58824', '건설워커 - PC'),
        (74321, 'M74321', '건설워커 - 모바일'),
        (49749, 'M49749', '교차로 - 모바일'),
        (41354, 'M41354', '교차로잡'),
        (158989, 'M158989', '교차로잡 - 모바일'),
        (128029, 'M128029', '꼬망세'),
        (23123, 'M23123', '다나와 - PC'),
        (87620, 'M87620', '다나와 - 모바일'),
        (168665, 'M168665', '다이닝코드 - PC'),
        (168666, 'M168666', '다이닝코드 - 모바일'),
        (14055, 'M14055', '닥터아파트'),
        (38329, 'M38329', '더어플'),
        (145966, 'M145966', '동원몰 - PC'),
        (145967, 'M145967', '동원몰 - 모바일'),
        (139215, 'M139215', '디시인사이드 - PC'),
        (131019, 'M131019', '디시인사이드 - 모바일'),
        (29978, 'M29978', '디올카페'),
        (67000, 'M67000', '디자이너잡'),
        (141121, 'M141121', '레포트샵'),
        (41352, 'M41352', '레포트월드'),
        (151173, 'M151173', '루리웹 - PC'),
        (151174, 'M151174', '루리웹 - 모바일'),
        (51655, 'M51655', '마이민트'),
        (137282, 'M137282', '마이민트 - 모바일'),
        (35324, 'M35324', '마이클럽'),
        (147491, 'M147491', '만개의레시피 - PC'),
        (26506, 'M26506', '맘스다이어리'),
        (58827, 'M58827', '메디업 - PC'),
        (62767, 'M62767', '메디업 - 모바일'),
        (37126, 'M37126', '메디잡 - PC'),
        (74320, 'M74320', '메디잡 - 모바일'),
        (58825, 'M58825', '메디컬잡'),
        (128030, 'M128030', '모바일만개의레시피'),
        (56345, 'M56345', '미디어잡'),
        (98128, 'M98128', '번개장터 - 모바일'),
        (15124, 'M15124', '벼룩시장 - PC'),
        (54186, 'M54186', '벼룩시장 - 모바일'),
        (16334, 'M16334', '부동산써브'),
        (84644, 'M84644', '비즈폼'),
        (27567, 'M27567', '뽐뿌 - PC'),
        (49745, 'M49745', '뽐뿌 - 모바일'),
        (69559, 'M69559', '사람인 - 모바일'),
        (69555, 'M69555', '샵마넷 - PC'),
        (69561, 'M69561', '샵마넷 - 모바일'),
        (69557, 'M69557', '샵오픈'),
        (156872, 'M156872', '셀잇 - PC'),
        (156873, 'M156873', '셀잇 - 모바일'),
        (141763, 'M141763', '쇼킹딜 - 모바일'),
        (62766, 'M62766', '수다닷컴'),
        (51654, 'M51654', '스누라이프'),
        (151175, 'M151175', '씽크존 - PC'),
        (20545, 'M20545', '아이베이비 - PC'),
        (49748, 'M49748', '아이베이비 - 모바일'),
        (18111, 'M18111', '안드로이드사이드'),
        (24087, 'M24087', '알바몬'),
        (15119, 'M15119', '알바천국 - PC'),
        (49746, 'M49746', '알바천국 - 모바일'),
        (36379, 'M36379', '에누리닷컴 - PC'),
        (45714, 'M45714', '에누리닷컴 - 모바일'),
        (137280, 'M137280', '에펨코리아'),
        (137281, 'M137281', '에펨코리아 - 모바일'),
        (79387, 'M79387', '여행오키'),
        (38193, 'M38193', '예스폼'),
        (70389, 'M70389', '오늘의유머'),
        (1526, 'M1526', '옥션'),
        (131018, 'M131018', '옥션 - 모바일'),
        (131268, 'M131268', '옥션중고장터 - 모바일'),
        (162341, 'M162341', '와글바글'),
        (49363, 'M49363', '웃긴대학'),
        (149196, 'M149196', '위메프 - 모바일'),
        (58826, 'M58826', '이엔지잡'),
        (37131, 'M37131', '이지데이 - PC'),
        (49747, 'M49747', '이지데이 - 모바일'),
        (37130, 'M37130', '이패스'),
        (38197, 'M38197', '인크루트 - PC'),
        (56346, 'M56346', '인크루트 - 모바일'),
        (16333, 'M16333', '인터넷교차로'),
        (35422, 'M35422', '인터파크 - PC'),
        (89270, 'M89270', '인터파크 - 모바일'),
        (38628, 'M38628', '일간스포츠'),
        (28552, 'M28552', '잡코리아 - PC'),
        (51271, 'M51271', '잡코리아 - 모바일'),
        (29983, 'M29983', '조선닷컴 - PC'),
        (46587, 'M46587', '조선닷컴 - 모바일'),
        (20808, 'M20808', '조아라'),
        (38627, 'M38627', '중앙일보'),
        (15604, 'M15604', '지식로그'),
        (29987, 'M29987', '채널A'),
        (20546, 'M20546', '쿠차'),
        (172112, 'M172112', '쿠차 - 모바일'),
        (39237, 'M39237', '쿠폰모아'),
        (19369, 'M19369', '클리앙'),
        (137283, 'M137283', '클리앙 - 모바일'),
        (15122, 'M15122', '키드키즈'),
        (69558, 'M69558', '패션워크'),
        (24086, 'M24086', '한겨레신문'),
        (20049, 'M20049', '한경닷컴 - PC'),
        (51591, 'M51591', '한경닷컴 - 모바일'),
        (106391, 'M106391', '해피캠퍼스 - PC'),
        (106392, 'M106392', '해피캠퍼스 - 모바일'),
        (156874, 'M156874', '해피학술 - PC'),
        (49362, 'M49362', '호텔모아'),
        (41353, 'M41353', '훈장마을 - PC'),
        (69560, 'M69560', '훈장마을 - 모바일'),
    )

    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP address'),
        db_index=True,
    )

    campaign_type = models.IntegerField(
        verbose_name=_('campaign type'),
        choices=CAMPAIGN_TYPE_CHOICES,
        default=1,
        db_index=True,
    )

    media = models.IntegerField(
        verbose_name=_('media'),
        choices=MEDIA_CHOICES,
        default=27758,
        db_index=True,
    )

    query = models.CharField(
        verbose_name=_('ad query'),
        max_length=255,
    )

    rank = models.IntegerField(
        verbose_name=_('ad rank'),
    )

    ad_group = models.CharField(
        verbose_name=_('ad group ID'),
        max_length=255,
    )

    ad = models.CharField(
        verbose_name=_('ad ID'),
        max_length=255,
    )

    keyword_id = models.CharField(
        verbose_name=_('ad keyword ID'),
        max_length=255,
    )

    keyword = models.CharField(
        verbose_name=_('ad keyword'),
        max_length=255,
    )

    user_agent = models.TextField(
        verbose_name=_('user-agent'),
        blank=True,
    )

    class Meta:
        verbose_name = _('naver advertisement log')
        verbose_name_plural = _('naver advertisement logs')

    def __str__(self):
        return '{}-{}-{}'.format(self.keyword, self.ip_address, self.created)


class MileageLog(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        db_index=True,
        on_delete=models.CASCADE,
    )

    order = models.ForeignKey(
        'shop.Order',
        verbose_name=_('order'),
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    mileage = models.DecimalField(
        verbose_name=_('mileage'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    memo = models.TextField(
        verbose_name=_('mileage memo'),
        blank=True,
    )

    class Meta:
        verbose_name = _('mileage log')
        verbose_name_plural = _('mileage logs')

    def __str__(self):
        return '{}-{}-{}'.format(self.user, self.user, self.created)

    def save(self, *args, **kwargs):
        profile = kwargs.pop('profile', True)

        super(MileageLog, self).save(*args, **kwargs)

        if profile:
            self.user.profile.mileage += self.mileage
            self.user.profile.save()


class PurchaseOrder(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    title = models.CharField(
        verbose_name=_('purchase order title'),
        max_length=255,
    )

    content = models.TextField(
        verbose_name=_('purchase order content'),
    )

    bank_account = models.CharField(
        verbose_name=_('purchase order bank account'),
        max_length=255,
        blank=True,
        null=True,
    )

    amount = models.DecimalField(
        verbose_name=_('purchase order amount'),
        max_digits=11,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    class Meta:
        verbose_name = _('purchase order')
        verbose_name_plural = _('purchase order')

    def __str__(self):
        return '{}-{}'.format(self.title, self.created)


class PurchaseOrderPayment(model_utils_models.SoftDeletableModel, model_utils_models.TimeStampedModel):
    ACCOUNT_CHOICES = Choices(
        (0, 'kb', _('KOOKMIN BANK')),
        (1, 'nh', _('NONGHYUP BANK')),
        (2, 'shinhan', _('SHINHAN BANK')),
        (3, 'woori', _('WOORI BANK')),
        (4, 'ibk', _('IBK BANK')),
    )

    order = models.ForeignKey(
        'shop.PurchaseOrder',
        verbose_name=_('order'),
        related_name='payments',
        db_index=True,
        on_delete=models.CASCADE,
    )

    account = models.IntegerField(
        verbose_name=_('account'),
        choices=ACCOUNT_CHOICES,
        default=ACCOUNT_CHOICES.kb,
        db_index=True,
    )

    amount = models.DecimalField(
        verbose_name=_('amount'),
        max_digits=11,
        decimal_places=2,
    )

    class Meta:
        verbose_name = _('purchase order payment')
        verbose_name_plural = _('purchase order payments')

    def __str__(self):
        return 'order - {} / payment - {} {} {}'.format(
            self.order.title, self.account, self.amount, self.created
        )
