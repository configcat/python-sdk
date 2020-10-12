from .constants import FEATURE_FLAGS, ROLLOUT_RULES, VARIATION_ID, VALUE, ROLLOUT_PERCENTAGE_ITEMS, CONFIG_FILE_NAME
from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import ConfigFetcher
from .configcache import InMemoryConfigCache
from .datagovernance import DataGovernance
from .rolloutevaluator import RolloutEvaluator
import logging
import sys
import hashlib
from collections import namedtuple

log = logging.getLogger(sys.modules[__name__].__name__)

KeyValue = namedtuple('KeyValue', 'key value')


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
                 proxy_auth=None,
                 data_governance=DataGovernance.Global):

        if sdk_key is None:
            raise ConfigCatClientException('SDK Key is required.')

        self._sdk_key = sdk_key
        self._rollout_evaluator = RolloutEvaluator()

        if config_cache_class:
            self._config_cache = config_cache_class()
        else:
            self._config_cache = InMemoryConfigCache()

        if poll_interval_seconds > 0:
            self._config_fetcher = ConfigFetcher(sdk_key, 'p', base_url, proxies, proxy_auth, data_governance)
            self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                        self.__get_cache_key(),
                                                        poll_interval_seconds, max_init_wait_time_seconds,
                                                        on_configuration_changed_callback)
        elif cache_time_to_live_seconds > 0:
            self._config_fetcher = ConfigFetcher(sdk_key, 'l', base_url, proxies, proxy_auth, data_governance)
            self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache,
                                                        self.__get_cache_key(),
                                                        cache_time_to_live_seconds)
        else:
            self._config_fetcher = ConfigFetcher(sdk_key, 'm', base_url, proxies, proxy_auth, data_governance)
            self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                          self.__get_cache_key())

    def get_value(self, key, default_value, user=None):
        config = self._cache_policy.get()
        if config is None:
            log.warning('Evaluating get_value(\'%s\') failed. Cache is empty. '
                        'Returning default_value in your get_value call: [%s].' %
                        (key, str(default_value)))
            return default_value

        value, variation_id = self._rollout_evaluator.evaluate(key, user, default_value, None, config)
        return value

    def get_all_keys(self):
        config = self._cache_policy.get()
        if config is None:
            return []

        feature_flags = config.get(FEATURE_FLAGS, None)
        if feature_flags is None:
            return []

        return list(feature_flags)

    def get_variation_id(self, key, default_variation_id, user=None):
        config = self._cache_policy.get()
        if config is None:
            log.warning('Evaluating get_variation_id(\'%s\') failed. Cache is empty. '
                        'Returning default_variation_id in your get_variation_id call: [%s].' %
                        (key, str(default_variation_id)))
            return default_variation_id

        value, variation_id = self._rollout_evaluator.evaluate(key, user, None, default_variation_id, config)
        return variation_id

    def get_all_variation_ids(self, user=None):
        keys = self.get_all_keys()
        variation_ids = []
        for key in keys:
            variation_id = self.get_variation_id(key, None, user)
            if variation_id is not None:
                variation_ids.append(variation_id)

        return variation_ids

    def get_key_and_value(self, variation_id):
        config = self._cache_policy.get()
        if config is None:
            log.warning('Evaluating get_key_and_value(\'%s\') failed. Cache is empty. '
                        'Returning None.' % variation_id)
            return None

        feature_flags = config.get(FEATURE_FLAGS, None)
        if feature_flags is None:
            log.warning('Evaluating get_key_and_value(\'%s\') failed. Cache is empty. '
                        'Returning None.' % variation_id)
            return None

        for key, value in list(feature_flags.items()):
            if variation_id == value.get(VARIATION_ID):
                return KeyValue(key, value[VALUE])

            rollout_rules = value.get(ROLLOUT_RULES, [])
            for rollout_rule in rollout_rules:
                if variation_id == rollout_rule.get(VARIATION_ID):
                    return KeyValue(key, rollout_rule[VALUE])

            rollout_percentage_items = value.get(ROLLOUT_PERCENTAGE_ITEMS, [])
            for rollout_percentage_item in rollout_percentage_items:
                if variation_id == rollout_percentage_item.get(VARIATION_ID):
                    return KeyValue(key, rollout_percentage_item[VALUE])

        log.error('Could not find the setting for the given variation_id: ' + variation_id)
        return None

    def force_refresh(self):
        self._cache_policy.force_refresh()

    def stop(self):
        self._cache_policy.stop()

    def __get_cache_key(self):
        return hashlib.sha1(('python_' + CONFIG_FILE_NAME + '_' + self._sdk_key).encode('utf-8'))
