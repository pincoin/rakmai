from django.db import models


class MessageQuerySet(models.QuerySet):
    def board(self, slug):
        return self.filter(board__slug=slug)

    def owner(self, owner):
        return self.filter(owner=owner)

    def published(self):
        return self.filter(status=self.model.STATUS_CHOICES.published, is_removed=False)

    def public(self):
        return self.filter(secret=False, is_removed=False)

    def secret(self):
        return self.filter(secret=True, is_removed=False)

    def deleted(self):
        return self.filter(is_removed=True)


class MessageManager(models.Manager):
    def get_queryset(self):
        return MessageQuerySet(self.model, using=self._db)

    def board(self, slug):
        return self.get_queryset().board(slug)

    def owner(self, owner):
        return self.get_queryset().owner(owner)

    def published(self):
        return self.get_queryset().published()

    def public(self):
        return self.get_queryset().public()

    def secret(self):
        return self.get_queryset().secret()

    def deleted(self):
        return self.get_queryset().deleted()
