from requests import HTTPError
import traceback

from .readwritelock import ReadWriteLock
from .interfaces import CachePolicy, ConfigCatLogger


class ManualPollingCachePolicy(CachePolicy):

    def __init__(self, config_fetcher, config_cache, logger: ConfigCatLogger):
        self._config_fetcher = config_fetcher
        self._config_cache = config_cache
        self._logger = logger
        self._lock = ReadWriteLock()

    def get(self):
        try:
            self._lock.acquire_read()

            config = self._config_cache.get()
            return config
        finally:
            self._lock.release_read()

    def force_refresh(self):
        try:
            configuration = self._config_fetcher.get_configuration_json()

            try:
                self._lock.acquire_write()

                self._config_cache.set(configuration)
            finally:
                self._lock.release_write()

        except HTTPError as e:
            self._logger.error('Double-check your API KEY at https://app.configcat.com/apikey.'
                               ' Received unexpected response: [%s]' % str(e.response))
        except:
            self._logger.error('Exception in ManualPollingCachePolicy.force_refresh: %s' % traceback.format_exc())

    def stop(self):
        pass
