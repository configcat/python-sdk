from .constants import FEATURE_FLAGS, ROLLOUT_RULES, VARIATION_ID, VALUE, ROLLOUT_PERCENTAGE_ITEMS, CONFIG_FILE_NAME
from .interfaces import ConfigCatClientException
from .lazyloadingcachepolicy import LazyLoadingCachePolicy
from .manualpollingcachepolicy import ManualPollingCachePolicy
from .autopollingcachepolicy import AutoPollingCachePolicy
from .configfetcher import ConfigFetcher
from .configcache import InMemoryConfigCache
from .configcatoptions import ConfigCatOptions
from .overridedatasource import OverrideBehaviour
from .pollingmode import AutoPollingMode, LazyLoadingMode
from .rolloutevaluator import RolloutEvaluator
import logging
import sys
import hashlib
from collections import namedtuple
import copy
import inspect

log = logging.getLogger(sys.modules[__name__].__name__)

KeyValue = namedtuple('KeyValue', 'key value')


def get_class_from_stack_frame(frame):
    args, _, _, value_dict = inspect.getargvalues(frame)
    # we check the first parameter for the frame function is
    # named 'self' or 'cls'
    if len(args):
        if args[0] == 'self':
            # in that case, 'self' will be referenced in value_dict
            instance = value_dict.get(args[0], None)
            if instance:
                # return its class
                return getattr(instance, '__class__', None)
        if args[0] == 'cls':
            # return the class
            return value_dict.get(args[0], None)

    # return None otherwise
    return None


def guard_call(allowed_classes, level=1):
    """
    Checks if the current method is being called from a method of certain classes.
    """
    stack_info = inspect.stack()[level + 1]
    frame = stack_info[0]
    calling_class = get_class_from_stack_frame(frame)
    if calling_class:
        for klass in allowed_classes:
            if issubclass(calling_class, klass):
                return True
    return False


class ConfigCatClient(object):
    _instances = {}

    @classmethod
    def get(cls, sdk_key, options=None):
        client = cls._instances.get(sdk_key)
        if client is not None:
            if options is not None:
                log.warning('Client for sdk_key %s is already created and will be reused; '
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

        if not guard_call([ConfigCatClient]):
            log.warning('ConfigCatClient.__init__() is deprecated. '
                        'Create the ConfigCat Client as a Singleton object with `ConfigCatClient.get()` instead')

        if sdk_key is None:
            raise ConfigCatClientException('SDK Key is required.')

        self._sdk_key = sdk_key
        self._default_user = options.default_user
        self._override_data_source = options.flag_overrides
        self._rollout_evaluator = RolloutEvaluator()

        self._config_cache = options.config_cache if options.config_cache is not None else InMemoryConfigCache()

        if self._override_data_source and self._override_data_source.get_behaviour() == OverrideBehaviour.LocalOnly:
            self._config_fetcher = None
            self._cache_policy = None
        else:
            if isinstance(options.polling_mode, AutoPollingMode):
                self._config_fetcher = ConfigFetcher(sdk_key,
                                                     options.polling_mode.identifier(),
                                                     options.base_url,
                                                     options.proxies, options.proxy_auth,
                                                     options.connect_timeout_seconds, options.read_timeout_seconds,
                                                     options.data_governance)
                self._cache_policy = AutoPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                            self.__get_cache_key(),
                                                            options.polling_mode.auto_poll_interval_seconds,
                                                            options.polling_mode.max_init_wait_time_seconds,
                                                            options.polling_mode.on_config_changed)
            elif isinstance(options.polling_mode, LazyLoadingMode):
                self._config_fetcher = ConfigFetcher(sdk_key,
                                                     options.polling_mode.identifier(),
                                                     options.base_url,
                                                     options.proxies, options.proxy_auth,
                                                     options.connect_timeout_seconds, options.read_timeout_seconds,
                                                     options.data_governance)
                self._cache_policy = LazyLoadingCachePolicy(self._config_fetcher, self._config_cache,
                                                            self.__get_cache_key(),
                                                            options.polling_mode.cache_refresh_interval_seconds)
            else:
                self._config_fetcher = ConfigFetcher(sdk_key,
                                                     options.polling_mode.identifier(),
                                                     options.base_url,
                                                     options.proxies, options.proxy_auth,
                                                     options.connect_timeout_seconds, options.read_timeout_seconds,
                                                     options.data_governance)
                self._cache_policy = ManualPollingCachePolicy(self._config_fetcher, self._config_cache,
                                                              self.__get_cache_key())

    def get_value(self, key, default_value, user=None):
        config = self.__get_settings()
        if config is None:
            log.warning('Evaluating get_value(\'%s\') failed. Cache is empty. '
                        'Returning default_value in your get_value call: [%s].' %
                        (key, str(default_value)))
            return default_value

        value, variation_id = self._rollout_evaluator.evaluate(key, user if user is not None else self._default_user, default_value, None, config)
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

        value, variation_id = self._rollout_evaluator.evaluate(key, user if user is not None else self._default_user, None, default_variation_id, config)
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
        return hashlib.sha1(('python_' + CONFIG_FILE_NAME + '_' + self._sdk_key).encode('utf-8')).hexdigest()
