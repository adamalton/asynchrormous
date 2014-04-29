AsynchrORMous
=============

A library which adds functionality for asynchronous database operations to Django's ORM


## Usage

###### 1. Create your model using the AsyncManager

```
from django.db import models
from asynchrormous import AsyncManager

class MyModel(models.Model):
    objects = AsyncManager() #This gives us async-capable querysets
    field1 = models.CharField(max_length=100)
```

###### 2. Query for your objects as normal, but add `.async()` into the chain.

This now gives you a queryset which when evaluated will do so asynchronously.

Note that you must add `.async()` **before** the queryset is evaluated, so for example it will be ineffective to add it after a `.count()` call.

```
queryset = MyModel.objects.filter(field1='cake').async()
```

###### 3. Cause the queryset to be evaluated, either in one of the normal ways, or with `.start()`.

The database operation will be done in the background, so you can continue to do other work while it is evaluating.

```
#E.g. this:
queryset = queryset[:10]
#or this:
queryset = queryset.start()

do_other_things()
```

We now have a queryset which is fetching its results in the background while our application continues to do other things.
When we are ready to iterate over the results we do so as normal:

```
for obj in queryset:
    print obj.field1
```

Note that we don't have to check if the queryset has fetched its results yet.  If it hasn't finished fetching its results by the time that we start iterating over it then it will just block until the results are fetched before iterating.

###### Using count()

Using `.count()` is slightly different because in the normal situation it would immediately return an integer.
With Asynchrormous it returns a `lazy` object, which will only block when you start to treat it as an `int`.
(For those not faimilar with `django.utils.functional.lazy` I recommend checking that out and using it to get a better idea of how this works.)

```
result = MyModel.objects.filter(field1='cake').aysnc().count()
do_other_things() #we can do this while the DB operation is happening asynchronously

if result > 1: #At this point, if the DB operation is not yet finished it will now block until it is.
    print "We have objects!"
```

