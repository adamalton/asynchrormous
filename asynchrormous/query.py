from threading import Thread
from django.db.models.query import QuerySet


class AsyncQuerySet(QuerySet):
    """ A queryset which allows DB operations to be pre-triggered so that they run in the
        background while the application can continue doing other processing.
    """

    def __init__(self, *args, **kwargs):
        super(AsyncQuerySet, self).__init__(*args, **kwargs)
        self._fetch_in_progress = False
        self._count_in_progress = False
        self._existence_check_in_progress = False
        #self._result_cache is already set as None by django anwyway
        self._count_result = None
        self._existence_result = None

    ###############################################################################################
    ############################################ API ##############################################

    def start_fetch(self):
        """ Trigger the asynchronous evaluation of this queryset in the backgroud.
            When it's finished, self._result_cache should be populated as normal.
        """
        self._fetch_in_progress = True
        self._fetch_all_in_thread()
        return self

    def start_count(self):
        """ Like start, but only does the necessary query which would be used for .count(). """
        self._count_in_progress = True
        self._count_in_thread()
        return self

    def start_exists(self):
        """ Like start, but only does the necessary query which would be used for .exists(). """
        self._existence_check_in_progress = True
        self._check_existence_in_thread()
        return self


    ###############################################################################################
    ############################### ASYNC CALLS, THREADING & WAITING ##############################

    def _fetch_all_in_thread(self):
        def run():
            len(self)
            #self._result_cache will be set by that ^
            self._fetch_in_progress = False
        self._run_in_thread(run)

    def _count_in_thread(self):
        def run():
            result = super(AsyncQuerySet, self).count()
            self._count_result = result
            self._count_in_progress = False
        self._run_in_thread(run)

    def _check_existence_in_thread(self):
        def run():
            result = super(AsyncQuerySet, self).exists()
            self._existence_result = result
            self._existence_check_in_progress = False
        self._run_in_thread(run)

    def _run_in_thread(self, function):
        Thread(target=function).start()


    ###############################################################################################
    ############################################ WAITING ##########################################

    def _wait_for_fetch_to_finish(self):
        self._wait_until_attr_is_false('_fetch_in_progress')

    def _wait_for_count_to_finish(self):
        self._wait_until_attr_is_false('_count_in_progress')

    def _wait_for_existence_check_to_finish(self):
        self._wait_until_attr_is_false('_existence_check_in_progress')

    def _wait_for_any_to_finish(self):
        while not (
            self._result_cache is None or self._count_result is None or self._existence_result is None
        ):
            pass

    def _wait_until_attr_is_false(self, attr):
        while getattr(self, attr):
            pass


    ###############################################################################################
    ############################ PREVENT DJANGO FROM DUPLICATING DB CALLS #########################

    def _fetch_all(self):
        if self._fetch_in_progress:
            self._wait_for_fetch_to_finish()
        super(AsyncQuerySet, self)._fetch_all()

    def exists(self):
        if self._existence_result is not None:
            return self._existence_result
        elif (
            self._fetch_in_progress or self._count_in_progress or self._existence_check_in_progress
        ):
            self._wait_for_any_to_finish()
            for attr in ('_result_cache', '_count_result', '_existence_result'):
                result = getattr(self, attr)
                if result is not None:
                    return bool(result)
        return super(AsyncQuerySet, self).exists()

    def count(self):
        if self._count_result is not None:
            return self._count_result
        elif self._count_in_progress:
            self._wait_for_count_to_finish()
            return self._count_result
        elif self._fetch_in_progress:
            self._wait_for_fetch_to_finish()
        return super(AsyncQuerySet, self).count() #This will use self._result_cache if possible

    def get(self, *args, **kwargs):
        #TODO: implement this.  It's not as simple as checking self._fetch_in_progress.
        #see QuerySet.get to find out why
        return super(AsyncQuerySet, self).get(*args, **kwargs)
