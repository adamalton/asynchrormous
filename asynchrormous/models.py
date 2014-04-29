from django.db import models
from asynchrormous.query import AsyncQuerySet


class AsyncManager(models.Manager):
    """ A model manager which uses the AsyncQuerySet. """

    def get_query_set(self):
        return AsyncQuerySet(self.model, using=self._db)
