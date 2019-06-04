from django.db import models


class PostQuerySet(models.QuerySet):
    def blog(self, blog_slug):
        return self.filter(blog__slug=blog_slug)

    def published(self):
        return self.filter(status=self.model.STATUS_CHOICES.published, is_removed=False)

    def draft(self):
        return self.filter(status=self.model.STATUS_CHOICES.draft, is_removed=False)

    def hidden(self):
        return self.filter(status=self.model.STATUS_CHOICES.hidden, is_removed=False)

    def deleted(self):
        return self.filter(is_removed=True)


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def blog(self, blog_slug):
        return self.get_queryset().blog(blog_slug)

    def published(self):
        return self.get_queryset().published()

    def draft(self):
        return self.get_queryset().draft()

    def hidden(self):
        return self.get_queryset().hidden()

    def deleted(self):
        return self.get_queryset().deleted()
