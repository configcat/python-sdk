import logging
import sys
import datetime
from requests import HTTPError

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
        self._cache_time_to_live = datetime.timedelta(seconds=cache_time_to_live_seconds)
        self._lock = ReadWriteLock()
        self._last_updated = None

    def get(self):
        config = None

        try:
            self._lock.acquire_read()

            config = self._config_cache.get(self._cache_key)

            utc_now = datetime.datetime.utcnow()
            if self._last_updated is not None and self._last_updated + self._cache_time_to_live > utc_now:
                if config is not None:
                    return config
        finally:
            self._lock.release_read()

        try:
            self._lock.acquire_write()
            # If while waiting to acquire the write lock another
            # thread has updated the content, then don't bother requesting
            # to the server to minimise time.
            if config is None or self._last_updated is None or self._last_updated + self._cache_time_to_live <= datetime.datetime.utcnow():
                force_fetch = not bool(config)
                self._force_refresh(force_fetch)
        finally:
            self._lock.release_write()

        try:
            self._lock.acquire_read()
            config = self._config_cache.get(self._cache_key)
            return config
        finally:
            self._lock.release_read()

    def force_refresh(self):
        force_fetch = False

        try:
            self._lock.acquire_read()
            config = self._config_cache.get(self._cache_key)
            force_fetch = not bool(config)
        finally:
            self._lock.release_read()

        try:
            self._lock.acquire_write()
            self._force_refresh(force_fetch)
        finally:
            self._lock.release_write()

    def _force_refresh(self, force_fetch):
        try:
            configuration_response = self._config_fetcher.get_configuration_json(force_fetch)
            # set _last_updated regardless of whether the cache is updated
            # or whether a 304 not modified has been sent back as the content
            # we have hasn't been updated on the server so not need
            # for subsequent requests to retry this within the cache time to live
            self._last_updated = datetime.datetime.utcnow()
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
