from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import ConfigFetcher
from .configcache import InMemoryConfigCache
from .rolloutevaluator import RolloutEvaluator
import logging
import sys

log = logging.getLogger(sys.modules[__name__].__name__)


class ConfigCatClient(object):

    def __init__(self,
                 sdk_key,
                 poll_interval_seconds=60,
                 max_init_wait_time_seconds=5,
                 on_configuration_changed_callback=None,
                 cache_time_to_live_seconds=60,
                 config_cache_class=None,
                 base_url=None,
                 proxies=None,
                 proxy_auth=None):

        if sdk_key is None:
            raise ConfigCatClientException('SDK Key is required.')

        self._sdk_key = sdk_key
        self._rollout_evaluator = RolloutEvaluator()

        if config_cache_class:
            self._config_cache = config_cache_class()
        else:
            self._config_cache = InMemoryConfigCache()

        if poll_interval_seconds > 0:
            self._config_fetcher = ConfigFetcher(sdk_key, 'p', base_url, proxies, proxy_auth)
            self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                        poll_interval_seconds, max_init_wait_time_seconds,
                                                        on_configuration_changed_callback)
        elif cache_time_to_live_seconds > 0:
            self._config_fetcher = ConfigFetcher(sdk_key, 'l', base_url, proxies, proxy_auth)
            self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache,
                                                        cache_time_to_live_seconds)
        else:
            self._config_fetcher = ConfigFetcher(sdk_key, 'm', base_url, proxies, proxy_auth)
            self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache)

    def get_value(self, key, default_value, user=None):
        config = self._cache_policy.get()
        if config is None:
            log.warning('Evaluating get_value(\'%s\') failed. Cache is empty. '
                        'Returning default_value in your get_value call: [%s].' %
                        (key, str(default_value)))
            return default_value

        return self._rollout_evaluator.evaluate(key, user, default_value, config)

    def get_all_keys(self):
        config = self._cache_policy.get()
        if config is None:
            return []

        return list(config)

    def force_refresh(self):
        self._cache_policy.force_refresh()

    def stop(self):
        self._cache_policy.stop()
