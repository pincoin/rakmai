from django.db import models


class BookQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status=self.model.STATUS_CHOICES.public)

    def private(self):
        return self.filter(status=self.model.STATUS_CHOICES.private)


class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)

    def public(self):
        return self.get_queryset().public()

    def private(self):
        return self.get_queryset().private()


class PageQuerySet(models.QuerySet):
    def book(self, book_pk):
        return self.filter(book__pk=book_pk)

    def draft(self):
        return self.filter(status=self.model.STATUS_CHOICES.draft)

    def public(self):
        from .models import Book  # no circular imports
        return self.filter(book__status=Book.STATUS_CHOICES.public,
                           status=self.model.STATUS_CHOICES.public)

    def private(self):
        return self.filter(status=self.model.STATUS_CHOICES.private)


class PageManager(models.Manager):
    def get_queryset(self):
        return PageQuerySet(self.model, using=self._db)

    def book(self, book_pk):
        return self.get_queryset().book(book_pk)

    def draft(self):
        return self.get_queryset().draft()

    def public(self):
        return self.get_queryset().public()

    def private(self):
        return self.get_queryset().private()
