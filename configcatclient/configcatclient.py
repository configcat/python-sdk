from configcatclient.logger import ConfigCatConsoleLogger
from configcatclient.user import User
from .interfaces import ConfigCatClientException, ConfigCatLogger, LogLevel
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import CacheControlConfigFetcher
from .configcache import InMemoryConfigCache
from .rolloutevaluator import RolloutEvaluator


class ConfigCatClient(object):

    def __init__(self,
                 api_key,
                 poll_interval_seconds=60,
                 max_init_wait_time_seconds=5,
                 on_configuration_changed_callback=None,
                 cache_time_to_live_seconds=60,
                 config_cache_class=None,
                 base_url=None,
                 log_level=LogLevel.WARNING,
                 logger: ConfigCatLogger = None):

        if api_key is None:
            raise ConfigCatClientException('API Key is required.')

        self._api_key = api_key

        if logger:
            self._logger = logger
        else:
            self._logger = ConfigCatConsoleLogger()

        self._logger.set_log_level(log_level)

        self._rollout_evaluator = RolloutEvaluator(self._logger)

        if config_cache_class:
            self._config_cache = config_cache_class()
        else:
            self._config_cache = InMemoryConfigCache()

        if poll_interval_seconds > 0:
            self._config_fetcher = CacheControlConfigFetcher(api_key, 'p', base_url)
            self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache, self._logger,
                                                        poll_interval_seconds, max_init_wait_time_seconds,
                                                        on_configuration_changed_callback)
        elif cache_time_to_live_seconds > 0:
            self._config_fetcher = CacheControlConfigFetcher(api_key, 'l', base_url)
            self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache, self._logger,
                                                        cache_time_to_live_seconds)
        else:
            self._config_fetcher = CacheControlConfigFetcher(api_key, 'm', base_url)
            self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache, self._logger)

    def get_value(self, key, default_value, user: User = None):
        config = self._cache_policy.get()
        if config is None:
            return default_value

        return self._rollout_evaluator.evaluate(key, user, default_value, config)

    def get_all_keys(self):
        config = self._cache_policy.get()
        if config is None:
            return []

        return list(config)

    def force_refresh(self):
        self._cache_policy.force_refresh()

    def set_log_level(self, log_level: LogLevel):
        self._logger.set_log_level(log_level)

    def stop(self):
        self._cache_policy.stop()
        self._config_fetcher.close()
