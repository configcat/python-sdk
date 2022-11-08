import logging
import sys
from datetime import datetime
from datetime import timedelta

from requests import HTTPError

from . import utils
from .configfetcher import FetchResponse
from .readwritelock import ReadWriteLock
from .interfaces import CachePolicy

log = logging.getLogger(sys.modules[__name__].__name__)


class LazyLoadingCachePolicy(CachePolicy):
    def __init__(self, config_fetcher, config_cache, cache_key, cache_time_to_live_seconds=60):
        if cache_time_to_live_seconds < 1:
            cache_time_to_live_seconds = 1
        self._config_fetcher = config_fetcher
        self._config_cache = config_cache
        self._cache_key = cache_key
        self._cache_time_to_live = timedelta(seconds=cache_time_to_live_seconds)
        self._lock = ReadWriteLock()

    def get(self):
        configuration = None
        etag = ''

        try:
            self._lock.acquire_read()

            configuration = self._config_cache.get(self._cache_key)

            utc_now = utils.get_utc_now()

            if configuration is not None:
                if datetime.utcfromtimestamp(configuration.get(FetchResponse.FETCH_TIME, 0)) + self._cache_time_to_live > utc_now:
                    return configuration.get(FetchResponse.CONFIG)
        finally:
            self._lock.release_read()

        try:
            self._lock.acquire_write()
            # If while waiting to acquire the write lock another
            # thread has updated the content, then don't bother requesting
            # to the server to minimise time.
            utc_now = utils.get_utc_now()
            if configuration is None or datetime.utcfromtimestamp(configuration.get(FetchResponse.FETCH_TIME, 0)) + self._cache_time_to_live <= utc_now:
                if bool(configuration):
                    etag = configuration.get(FetchResponse.ETAG, '')
                self._force_refresh(etag)
        finally:
            self._lock.release_write()

        try:
            self._lock.acquire_read()
            configuration = self._config_cache.get(self._cache_key)
            return configuration.get(FetchResponse.CONFIG) if configuration else None
        finally:
            self._lock.release_read()

    def force_refresh(self, etag=''):
        try:
            self._lock.acquire_read()
            configuration = self._config_cache.get(self._cache_key)
            if bool(configuration):
                etag = configuration.get(FetchResponse.ETAG, '')
        finally:
            self._lock.release_read()

        try:
            self._lock.acquire_write()
            self._force_refresh(etag)
        finally:
            self._lock.release_write()

    def _force_refresh(self, etag):
        try:
            configuration_response = self._config_fetcher.get_configuration_json(etag)
            # set _config_cache regardless of whether the cache is updated
            # or whether a 304 not modified has been sent back as the content
            # we have hasn't been updated on the server so not need
            # for subsequent requests to retry this within the cache time to live
            if configuration_response.is_fetched():
                configuration = configuration_response.json()
                self._config_cache.set(self._cache_key, configuration)
        except HTTPError as e:
            log.error('Double-check your SDK Key at https://app.configcat.com/sdkkey.'
                      ' Received unexpected response: %s' % str(e.response))
        except Exception:
            log.exception(sys.exc_info()[0])

    def stop(self):
        pass
