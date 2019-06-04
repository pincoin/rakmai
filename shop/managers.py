from django.db import models


class ProductQuerySet(models.QuerySet):
    def store(self, store_code):
        return self.filter(store__code=store_code)

    def enabled(self):
        return self.filter(status=self.model.STATUS_CHOICES.enabled, is_removed=False)

    def disabled(self):
        return self.filter(status=self.model.STATUS_CHOICES.disabled, is_removed=False)

    def available(self):
        return self.filter(stock=self.model.STOCK_CHOICES.in_stock, is_removed=False)

    def unavailable(self):
        return self.filter(stock=self.model.STOCK_CHOICES.sold_out, is_removed=False)


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def store(self, store_code):
        return self.get_queryset().store(store_code)

    def enabled(self):
        return self.get_queryset().enabled()

    def disabled(self):
        return self.get_queryset().disabled()

    def available(self):
        return self.get_queryset().available()

    def unavailable(self):
        return self.get_queryset().unavailable()


class OrderQuerySet(models.QuerySet):
    def valid(self, user):
        return self.filter(user=user, is_removed=False, visible=self.model.VISIBLE_CHOICES.visible)

    def pending(self):
        return self.filter(status=self.model.STATUS_CHOICES.payment_pending)

    def shipped(self):
        return self.filter(status=self.model.STATUS_CHOICES.shipped)

    def deleted(self):
        return self.filter(is_removed=True)


class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)

    def valid(self, user):
        return self.get_queryset().valid(user)

    def pending(self):
        return self.get_queryset().pending()

    def shipped(self):
        return self.get_queryset().shipped()

    def deleted(self):
        return self.get_queryset().deleted()
