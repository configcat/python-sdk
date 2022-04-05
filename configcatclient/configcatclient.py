from .constants import FEATURE_FLAGS, ROLLOUT_RULES, VARIATION_ID, VALUE, ROLLOUT_PERCENTAGE_ITEMS, CONFIG_FILE_NAME
from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import ConfigFetcher
from .configcache import InMemoryConfigCache
from .datagovernance import DataGovernance
from .overridedatasource import OverrideBehaviour
from .rolloutevaluator import RolloutEvaluator
import logging
import sys
import hashlib
from collections import namedtuple
import copy

log = logging.getLogger(sys.modules[__name__].__name__)

KeyValue = namedtuple('KeyValue', 'key value')


class ConfigCatClient(object):
    sdk_keys = []

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
                 connect_timeout=10,
                 read_timeout=30,
                 flag_overrides=None,
                 data_governance=DataGovernance.Global):

        if sdk_key is None:
            raise ConfigCatClientException('SDK Key is required.')

        if sdk_key in ConfigCatClient.sdk_keys:
            log.warning('A ConfigCat Client is already initialized with sdk_key %s. '
                        'We strongly recommend you to use the ConfigCat Client as '
                        'a Singleton object in your application.' % sdk_key)
        else:
            ConfigCatClient.sdk_keys.append(sdk_key)

        self._sdk_key = sdk_key
        self._override_data_source = flag_overrides
        self._rollout_evaluator = RolloutEvaluator()

        if config_cache_class:
            self._config_cache = config_cache_class()
        else:
            self._config_cache = InMemoryConfigCache()

        if self._override_data_source and self._override_data_source.get_behaviour() == OverrideBehaviour.LocalOnly:
            self._config_fetcher = None
            self._cache_policy = None
        else:
            if poll_interval_seconds > 0:
                self._config_fetcher = ConfigFetcher(sdk_key, 'p', base_url, proxies, proxy_auth, connect_timeout, read_timeout, data_governance)
                self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                            self.__get_cache_key(),
                                                            poll_interval_seconds, max_init_wait_time_seconds,
                                                            on_configuration_changed_callback)
            elif cache_time_to_live_seconds > 0:
                self._config_fetcher = ConfigFetcher(sdk_key, 'l', base_url, proxies, proxy_auth, connect_timeout, read_timeout, data_governance)
                self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache,
                                                            self.__get_cache_key(),
                                                            cache_time_to_live_seconds)
            else:
                self._config_fetcher = ConfigFetcher(sdk_key, 'm', base_url, proxies, proxy_auth, connect_timeout, read_timeout, data_governance)
                self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                              self.__get_cache_key())

    def get_value(self, key, default_value, user=None):
        config = self.__get_settings()
        if config is None:
            log.warning('Evaluating get_value(\'%s\') failed. Cache is empty. '
                        'Returning default_value in your get_value call: [%s].' %
                        (key, str(default_value)))
            return default_value

        value, variation_id = self._rollout_evaluator.evaluate(key, user, default_value, None, config)
        return value

    def get_all_keys(self):
        config = self.__get_settings()
        if config is None:
            return []

        feature_flags = config.get(FEATURE_FLAGS, None)
        if feature_flags is None:
            return []

        return list(feature_flags)

    def get_variation_id(self, key, default_variation_id, user=None):
        config = self.__get_settings()
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
        config = self.__get_settings()
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

    def get_all_values(self, user=None):
        keys = self.get_all_keys()
        all_values = {}
        for key in keys:
            value = self.get_value(key, None, user)
            if value is not None:
                all_values[key] = value

        return all_values

    def force_refresh(self):
        if self._cache_policy:
            self._cache_policy.force_refresh()

    def stop(self):
        if self._cache_policy:
            self._cache_policy.stop()
        ConfigCatClient.sdk_keys.remove(self._sdk_key)

    def __get_settings(self):
        if self._override_data_source:
            behaviour = self._override_data_source.get_behaviour()

            if behaviour == OverrideBehaviour.LocalOnly:
                return self._override_data_source.get_overrides()
            elif behaviour == OverrideBehaviour.RemoteOverLocal:
                remote_settings = self._cache_policy.get()
                local_settings = self._override_data_source.get_overrides()
                result = copy.deepcopy(local_settings)
                if FEATURE_FLAGS in remote_settings and FEATURE_FLAGS in local_settings:
                    result[FEATURE_FLAGS].update(remote_settings[FEATURE_FLAGS])
                return result
            elif behaviour == OverrideBehaviour.LocalOverRemote:
                remote_settings = self._cache_policy.get()
                local_settings = self._override_data_source.get_overrides()
                result = copy.deepcopy(remote_settings)
                if FEATURE_FLAGS in remote_settings and FEATURE_FLAGS in local_settings:
                    result[FEATURE_FLAGS].update(local_settings[FEATURE_FLAGS])
                return result

        return self._cache_policy.get()

    def __get_cache_key(self):
        return hashlib.sha1(('python_' + CONFIG_FILE_NAME + '_' + self._sdk_key).encode('utf-8'))
