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

###### 2. Create your queryset as normal.

Note that you do not want to  evaluate the queryset yet, as that would default the point of having the async magic.

```
queryset = MyModel.objects.filter(field1='cake')
```

###### 3. Trigger the asynchronous database operation for whichever evaulation you require.

There are 3 possible database operations which you can trigger:

1. Fetching of results using `.start_fetch()`.  This is for when you plan to iterate over the results or call `len()` on the queryset.
2. Fetching of the count using `start_count()`.  This is for when you plan to call `.count()` on the queryset.
3. Fetching of the existence/non-zero-ness using `start_exists()`.  This is for when you plan to call `.exists()` on the queryset.

The releveant database operation will then be started in the background, allowing your application to continue to do other work while the database operation is in progress in the background.


###### 4. Use your queryset as normal to get the results:

You can now iterate over your queryset, call `.count()`, `.exists()` or `len()` on it as normal.  If the database operation which you triggered earlier has not yet finished then it will now block (as Django normally would) until it has finished.

### Examples

```
queryset = MyModel.objects.filter(field1='cake')[:10].start_fetch()
do_other_things() #This happens in parallel to the database operation
for obj in queryset:
    print object

queryset = MyModel.objects.filter(field1='sausage').start_count()
do_other_things() #This happens in parallel to the database operation
if queryset.count() > 2:
    print "We have many sausages"

queryset = MyModel.objects.filter(field1='miracle').start_exists()
do_other_things() #This happens in parallel to the database operation
if queryset.exists():
    print "We have a miracle!"
```


## TODO

* Add an `async_get()` method.  If you look in `django.db.models.query.QuerySet.get` you'll see why this would be a good idea.
* Add more examples, including calling `len()` and `bool()` on the queryset, using `.exists()` after calling `.start_fetch()` (which would work), etc.
