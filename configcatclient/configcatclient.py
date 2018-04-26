from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import CacheControlConfigFetcher
from .configcache import InMemoryConfigCache


class ConfigCatClient(object):
    """
     A client for handling configurations provided by ConfigCat.
    """

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

    def get_configuration_json(self):
        """
        Gets the configuration.
        :return: the configuration. Returns None if the configuration fetch from the network fails.
        """
        return self._cache_policy.get()

    def get_value(self, key, default_value):
        """  Gets a value from the configuration identified by the given key.
        :param key: the identifier of the configuration value.
        :param default_value: in case of any failure, this value will be returned.
        :return: the configuration value identified by the given key.
        """
        config = self._cache_policy.get()
        if config is None or key not in config:
            return default_value

        return config[key]

    def force_refresh(self):
        """
        """
        self._cache_policy.force_refresh()

    def stop(self):
        """
        """
        self._cache_policy.stop()
        self._config_fetcher.close()
