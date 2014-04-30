from django.db import models
from django.test import TestCase

from asynchrormous.models import AsyncManager
from asynchrormous.query import AsyncQuerySet


class AsyncModel(models.Model):
    objects = AsyncManager()
    field1 = models.IntegerField(default=0)
    field2 = models.CharField(max_length=100)


class BasicBehaviourTest(TestCase):
        """ Test that calling start_<thing>() on the queryset and then using it as normal works as
            normal.  This doesn't not test the asynchronicity, only that it doesn't break.
        """

        def setUp(self):
            self.objects = []
            #deliberately create loads of objects so that queries take a notable amount
            #of time so that threading is tested
            for x in xrange(1000):
                self.objects.append(AsyncModel.objects.create(field1=x % 2))

        def test_start_fetch(self):
            normal_result = list(AsyncModel.objects.filter(field1=0))
            qs = AsyncModel.objects.filter(field1=0)
            qs.start_fetch()
            self.assertEqual(list(qs), normal_result)

        def test_start_count(self):
            normal_result = AsyncModel.objects.filter(field1=1).count()
            qs = AsyncModel.objects.filter(field1=0)
            qs.start_count()
            self.assertEqual(qs.count(), normal_result)

        def test_start_exists(self):
            for value in (1, 7): #one that exists, one that doesn't
                normal_result = AsyncModel.objects.filter(field1=value).exists()
                qs = AsyncModel.objects.filter(field1=value)
                qs.start_exists()
                self.assertEqual(qs.exists(), normal_result)


class CloneTest(TestCase):
    """ Test aspects of the queryset's cloning behaviour. """

    def test_start_methods_return_queryset(self):
        """ Test that calling .start_<thing>() on the queryset returns the queryset. """
        qs = AsyncModel.objects.all().start_fetch()
        #Check that the queryset is the right class
        self.assertEqual(qs.__class__, AsyncQuerySet)
        #Check that it is the same queryset that is having/had its results fetched, not a new clone
        self.assertTrue(qs._fetch_thread or qs._result_cache is not None)
        #Ditto for start_count() and start_exists()...
        qs = AsyncModel.objects.all().start_count()
        self.assertEqual(qs.__class__, AsyncQuerySet)
        self.assertTrue(qs._count_thread or qs._count_result is not None)
        qs = AsyncModel.objects.all().start_exists()
        self.assertEqual(qs.__class__, AsyncQuerySet)
        self.assertTrue(qs._exists_thread or qs._existence_result is not None)



