from threading import Thread
from django.db.models.query import QuerySet


class AsyncQuerySet(QuerySet):
    """ A queryset which allows DB operations to be pre-triggered so that they run in the
        background while the application can continue doing other processing.
    """

    def __init__(self, *args, **kwargs):
        super(AsyncQuerySet, self).__init__(*args, **kwargs)
        self._fetch_thread = None
        self._count_thread = None
        self._exists_thread = None
        #self._result_cache is already set as None by django anwyway
        self._count_result = None
        self._exists_result = None

    ###############################################################################################
    ############################################ API ##############################################

    def start_fetch(self):
        """ Trigger the asynchronous evaluation of this queryset in the backgroud.
            When it's finished, self._result_cache should be populated as normal.
        """
        thread = Thread(target=self._do_fetch)
        thread.start()
        self._fetch_thread = thread
        return self

    def start_count(self):
        """ Like start, but only does the necessary query which would be used for .count(). """
        thread = Thread(target=self._do_count)
        thread.start()
        self._count_thread = thread
        return self

    def start_exists(self):
        """ Like start, but only does the necessary query which would be used for .exists(). """
        thread = Thread(target=self._do_exists)
        thread.start()
        self._exists_thread = thread
        return self


    ###############################################################################################
    ############################### ASYNC CALLS, THREADING & WAITING ##############################

    def _do_fetch(self):
        len(self)
        #self._result_cache will be set by that ^

    def _do_count(self):
        result = super(AsyncQuerySet, self).count()
        self._count_result = result

    def _do_exists(self):
        result = super(AsyncQuerySet, self).exists()
        self._exists_result = result

    def _wait_for_any_to_finish(self):
        """ Starting with the one which is most likely to be the fastest, find the first thread
            which exists and wait for it to finish.
        """
        for thread in (self._exists_thread, self._count_thread, self._fetch_thread):
            if thread:
                thread.join()


    ###############################################################################################
    ############################ PREVENT DJANGO FROM DUPLICATING DB CALLS #########################

    def _fetch_all(self):
        if self._fetch_thread:
            self._fetch_thread.join() #Wait until it's done
        super(AsyncQuerySet, self)._fetch_all()

    def exists(self):
        if self._exists_result is not None:
            return self._exists_result
        elif (
            #If we have any of our queries currently running
            self._fetch_thread or self._count_thread or self._exists_thread
        ):
            self._wait_for_any_to_finish()
            for attr in ('_result_cache', '_count_result', '_exists_result'):
                result = getattr(self, attr)
                if result is not None:
                    return bool(result)
        return super(AsyncQuerySet, self).exists()

    def count(self):
        if self._count_result is not None:
            return self._count_result
        elif self._count_thread:
            self._count_thread.join() #Wait for it to finish
            return self._count_result
        elif self._fetch_thread:
            self._fetch_thread.join() #Wait for it to finish
        return super(AsyncQuerySet, self).count() #This will use self._result_cache if possible

    def get(self, *args, **kwargs):
        #TODO: implement this.  It's not as simple as checking self._fetch_in_progress.
        #see QuerySet.get to find out why
        return super(AsyncQuerySet, self).get(*args, **kwargs)
