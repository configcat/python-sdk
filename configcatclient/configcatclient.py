from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import CacheControlConfigFetcher
from .configcache import InMemoryConfigCache
from .rolloutevaluator import RolloutEvaluator
import logging
import sys

log = logging.getLogger(sys.modules[__name__].__name__)


class ConfigCatClient(object):

    def __init__(self,
                 api_key,
                 poll_interval_seconds=60,
                 max_init_wait_time_seconds=5,
                 on_configuration_changed_callback=None,
                 cache_time_to_live_seconds=60,
                 config_cache_class=None):

        if api_key is None:
            raise ConfigCatClientException('API Key is required.')

        self._api_key = api_key

        if config_cache_class:
            self._config_cache = config_cache_class()
        else:
            self._config_cache = InMemoryConfigCache()

        if poll_interval_seconds > 0:
            self._config_fetcher = CacheControlConfigFetcher(api_key, 'p')
            self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache, poll_interval_seconds,
                                                        max_init_wait_time_seconds, on_configuration_changed_callback)
        elif cache_time_to_live_seconds > 0:
            self._config_fetcher = CacheControlConfigFetcher(api_key, 'l')
            self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache,
                                                        cache_time_to_live_seconds)
        else:
            self._config_fetcher = CacheControlConfigFetcher(api_key, 'm')
            self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache)

    def get_value(self, key, default_value, user=None):
        config = self._cache_policy.get()
        if config is None:
            return default_value

        return RolloutEvaluator.evaluate(key, user, default_value, config)

    def force_refresh(self):
        self._cache_policy.force_refresh()

    def stop(self):
        self._cache_policy.stop()
        self._config_fetcher.close()
