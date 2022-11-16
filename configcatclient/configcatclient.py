from .constants import FEATURE_FLAGS, ROLLOUT_RULES, VARIATION_ID, VALUE, ROLLOUT_PERCENTAGE_ITEMS, CONFIG_FILE_NAME
from .evaluationdetails import EvaluationDetails
from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .logger import Logger
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import ConfigFetcher
from .configcache import InMemoryConfigCache
from .configcatoptions import ConfigCatOptions, Hooks
from .overridedatasource import OverrideBehaviour
from .pollingmode import AutoPollingMode, LazyLoadingMode
from .rolloutevaluator import RolloutEvaluator
import hashlib
from collections import namedtuple
import copy
from .utils import method_is_called_from, get_date_time

KeyValue = namedtuple('KeyValue', 'key value')


class ConfigCatClient(object):
    _instances = {}

    @classmethod
    def get(cls, sdk_key, options=None):
        client = cls._instances.get(sdk_key)
        if client is not None:
            if options is not None:
                client.log.warning('Client for sdk_key `%s` is already created and will be reused; '
                                   'options passed are being ignored.' % sdk_key)
            return client

        if options is None:
            options = ConfigCatOptions()

        client = ConfigCatClient(sdk_key=sdk_key,
                                 options=options)
        cls._instances[sdk_key] = client
        return client

    @classmethod
    def close_all(cls):
        # Closes all ConfigCatClient instances.
        for key, value in list(cls._instances.items()):
            value.close_resources()
        cls._instances.clear()

    def __init__(self,
                 sdk_key,
                 options=ConfigCatOptions()):

        self._hooks = options.hooks if options.hooks is not None else Hooks()
        self.log = Logger('configcat', self._hooks)

        if not method_is_called_from(ConfigCatClient.get):
            self.log.warning('ConfigCatClient.__init__() is deprecated. '
                             'Create the ConfigCat Client as a Singleton object with `ConfigCatClient.get()` instead')

        if sdk_key is None:
            raise ConfigCatClientException('SDK Key is required.')

        self._sdk_key = sdk_key
        self._default_user = options.default_user
        self._rollout_evaluator = RolloutEvaluator(self.log)
        if options.flag_overrides:
            self._override_data_source = options.flag_overrides.create_data_source(self.log)
        else:
            self._override_data_source = None

        self._config_cache = options.config_cache if options.config_cache is not None else InMemoryConfigCache()

        if self._override_data_source and self._override_data_source.get_behaviour() == OverrideBehaviour.LocalOnly:
            self._config_fetcher = None
            self._cache_policy = None
        else:
            self._config_fetcher = ConfigFetcher(self._sdk_key,
                                                 self.log,
                                                 options.polling_mode.identifier(),
                                                 options.base_url,
                                                 options.proxies, options.proxy_auth,
                                                 options.connect_timeout_seconds, options.read_timeout_seconds,
                                                 options.data_governance)
            if isinstance(options.polling_mode, AutoPollingMode):
                self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                            self.__get_cache_key(), self.log, self._hooks,
                                                            options.polling_mode.auto_poll_interval_seconds,
                                                            options.polling_mode.max_init_wait_time_seconds,
                                                            options.polling_mode.on_config_changed)
            elif isinstance(options.polling_mode, LazyLoadingMode):
                self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache,
                                                            self.__get_cache_key(), self.log, self._hooks,
                                                            options.polling_mode.cache_refresh_interval_seconds)
            else:
                self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                              self.__get_cache_key(), self.log, self._hooks)

    def get_value(self, key, default_value, user=None):
        config, fetch_time = self.__get_settings()
        if config is None:
            message = 'Evaluating get_value(\'{}\') failed. Cache is empty. ' \
                      'Returning default_value in your get_value call: [{}].'.format(key, str(default_value))
            self.log.error(message)
            self._hooks.invoke_on_flag_evaluated(EvaluationDetails.from_error(key, default_value, message))
            return default_value

        details = self.__evaluate(key=key,
                                  user=user,
                                  default_value=default_value,
                                  default_variation_id=None,
                                  config=config,
                                  fetch_time=fetch_time)

        return details.value

    def get_value_details(self, key, default_value, user=None):
        config, fetch_time = self.__get_settings()
        if config is None:
            message = 'Evaluating get_value(\'{}\') failed. Cache is empty. ' \
                      'Returning default_value in your get_value call: [{}].'.format(key, str(default_value))
            self.log.error(message)
            details = EvaluationDetails.from_error(key, default_value, message)
            self._hooks.invoke_on_flag_evaluated(details)
            return details

        details = self.__evaluate(key=key,
                                  user=user,
                                  default_value=default_value,
                                  default_variation_id=None,
                                  config=config,
                                  fetch_time=fetch_time)

        return details

    def get_all_keys(self):
        config, _ = self.__get_settings()
        if config is None:
            return []

        feature_flags = config.get(FEATURE_FLAGS, None)
        if feature_flags is None:
            return []

        return list(feature_flags)

    def get_variation_id(self, key, default_variation_id, user=None):
        config, fetch_time = self.__get_settings()
        if config is None:
            message = 'Evaluating get_variation_id(\'{}\') failed. Cache is empty. ' \
                      'Returning default_variation_id in your get_variation_id call: ' \
                      '[{}].'.format(key, str(default_variation_id))
            self.log.error(message)
            self._hooks.invoke_on_flag_evaluated(EvaluationDetails.from_error(key, None, message, default_variation_id))
            return default_variation_id

        details = self.__evaluate(key=key,
                                  user=user,
                                  default_value=None,
                                  default_variation_id=default_variation_id,
                                  config=config,
                                  fetch_time=fetch_time)
        return details.variation_id

    def get_all_variation_ids(self, user=None):
        keys = self.get_all_keys()
        variation_ids = []
        for key in keys:
            variation_id = self.get_variation_id(key, None, user)
            if variation_id is not None:
                variation_ids.append(variation_id)

        return variation_ids

    def get_key_and_value(self, variation_id):
        config, _ = self.__get_settings()
        if config is None:
            self.log.warning('Evaluating get_key_and_value(\'%s\') failed. Cache is empty. '
                             'Returning None.' % variation_id)
            return None

        feature_flags = config.get(FEATURE_FLAGS, None)
        if feature_flags is None:
            self.log.warning('Evaluating get_key_and_value(\'%s\') failed. Cache is empty. '
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

        self.log.error('Could not find the setting for the given variation_id: ' + variation_id)
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

    def set_default_user(self, user):
        self._default_user = user

    def clear_default_user(self):
        self._default_user = None

    def close_resources(self):
        if self._cache_policy:
            self._cache_policy.stop()

    def close(self):
        self.close_resources()
        ConfigCatClient._instances.pop(self._sdk_key)

    def __get_settings(self):
        if self._override_data_source:
            behaviour = self._override_data_source.get_behaviour()

            if behaviour == OverrideBehaviour.LocalOnly:
                return self._override_data_source.get_overrides(), None
            elif behaviour == OverrideBehaviour.RemoteOverLocal:
                remote_settings, fetch_time = self._cache_policy.get()
                local_settings = self._override_data_source.get_overrides()
                result = copy.deepcopy(local_settings)
                if FEATURE_FLAGS in remote_settings and FEATURE_FLAGS in local_settings:
                    result[FEATURE_FLAGS].update(remote_settings[FEATURE_FLAGS])
                return result, fetch_time
            elif behaviour == OverrideBehaviour.LocalOverRemote:
                remote_settings, fetch_time = self._cache_policy.get()
                local_settings = self._override_data_source.get_overrides()
                result = copy.deepcopy(remote_settings)
                if FEATURE_FLAGS in remote_settings and FEATURE_FLAGS in local_settings:
                    result[FEATURE_FLAGS].update(local_settings[FEATURE_FLAGS])
                return result, fetch_time

        return self._cache_policy.get()

    def __get_cache_key(self):
        return hashlib.sha1(('python_' + CONFIG_FILE_NAME + '_' + self._sdk_key).encode('utf-8')).hexdigest()

    def __evaluate(self, key, user, default_value, default_variation_id, config, fetch_time):
        user = user if user is not None else self._default_user
        value, variation_id, rule, percentage_rule, error = self._rollout_evaluator.evaluate(
            key=key,
            user=user,
            default_value=default_value,
            default_variation_id=default_variation_id,
            config=config)

        details = EvaluationDetails(key=key,
                                    value=value,
                                    variation_id=variation_id,
                                    fetch_time=get_date_time(fetch_time) if fetch_time is not None else None,
                                    user=user,
                                    is_default_value=True if error else False,
                                    error=error,
                                    matched_evaluation_rule=rule,
                                    matched_evaluation_percentage_rule=percentage_rule)
        self._hooks.invoke_on_flag_evaluated(details)
        return details
