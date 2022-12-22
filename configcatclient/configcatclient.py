from threading import Lock

from . import utils
from .configservice import ConfigService
from .constants import ROLLOUT_RULES, VARIATION_ID, VALUE, ROLLOUT_PERCENTAGE_ITEMS, CONFIG_FILE_NAME
from .evaluationdetails import EvaluationDetails
from .interfaces import ConfigCatClientException
from .logger import Logger
from .configfetcher import ConfigFetcher
from .configcache import NullConfigCache
from .configcatoptions import ConfigCatOptions, Hooks
from .overridedatasource import OverrideBehaviour
from .refreshresult import RefreshResult
from .rolloutevaluator import RolloutEvaluator
import hashlib
from collections import namedtuple
import copy
from .utils import method_is_called_from, get_date_time

KeyValue = namedtuple('KeyValue', 'key value')


class ConfigCatClient(object):
    _lock = Lock()
    _instances = {}

    @classmethod
    def get(cls, sdk_key, options=None):
        """
        Creates a new or gets an already existing `ConfigCatClient` for the given `sdk_key`.

        :param sdk_key: ConfigCat SDK Key to access your configuration.
        :param options: Configuration `ConfigCatOptions` for `ConfigCatClient`.
        :return: the `ConfigCatClient` instance.
        """
        with cls._lock:
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
        """
        Closes all ConfigCatClient instances.
        """
        with cls._lock:
            for key, value in list(cls._instances.items()):
                value.__close_resources()
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

        self._config_cache = options.config_cache if options.config_cache is not None else NullConfigCache()

        if self._override_data_source and self._override_data_source.get_behaviour() == OverrideBehaviour.LocalOnly:
            self._config_fetcher = None
            self._config_service = None
        else:
            self._config_fetcher = ConfigFetcher(self._sdk_key,
                                                 self.log,
                                                 options.polling_mode.identifier(),
                                                 options.base_url,
                                                 options.proxies, options.proxy_auth,
                                                 options.connect_timeout_seconds, options.read_timeout_seconds,
                                                 options.data_governance)
            self._config_service = ConfigService(self._sdk_key,
                                                 options.polling_mode,
                                                 self._hooks,
                                                 self._config_fetcher,
                                                 self.log,
                                                 self._config_cache,
                                                 options.offline)

    def get_value(self, key, default_value, user=None):
        """
        Gets the value of a feature flag or setting identified by the given `key`.

        :param key: the identifier of the feature flag or setting.
        :param default_value: in case of any failure, this value will be returned.
        :param user: the user object to identify the caller.
        :return: the value.
        """
        settings, fetch_time = self.__get_settings()
        if settings is None:
            message = 'Evaluating get_value(\'{}\') failed. Cache is empty. ' \
                      'Returning default_value in your get_value call: [{}].'.format(key, str(default_value))
            self.log.error(message)
            self._hooks.invoke_on_flag_evaluated(EvaluationDetails.from_error(key, default_value, message))
            return default_value

        details = self.__evaluate(key=key,
                                  user=user,
                                  default_value=default_value,
                                  default_variation_id=None,
                                  settings=settings,
                                  fetch_time=fetch_time)

        return details.value

    def get_value_details(self, key, default_value, user=None):
        """
        Gets the value and evaluation details of a feature flag or setting identified by the given `key`.

        :param key: the identifier of the feature flag or setting.
        :param default_value: in case of any failure, this value will be returned.
        :param user: the user object to identify the caller.
        :return: the evaluation details.
        """
        settings, fetch_time = self.__get_settings()
        if settings is None:
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
                                  settings=settings,
                                  fetch_time=fetch_time)

        return details

    def get_all_keys(self):
        """
        Gets all setting keys.

        :return: list of keys.
        """
        settings, _ = self.__get_settings()
        if settings is None:
            return []

        return list(settings)

    def get_variation_id(self, key, default_variation_id, user=None):
        """
        Gets the Variation ID (analytics) of a feature flag or setting based on it's key.

        :param key: the identifier of the feature flag or setting.
        :param default_variation_id: in case of any failure, this value will be returned.
        :param user: the user object to identify the caller.
        :return: the variation ID.
        """
        self.log.warning('get_variation_id is deprecated and will be removed in a future major version. '
                         'Please use [get_value_details] instead.')

        settings, fetch_time = self.__get_settings()
        if settings is None:
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
                                  settings=settings,
                                  fetch_time=fetch_time)
        return details.variation_id

    def get_all_variation_ids(self, user=None):
        """
        Gets the Variation IDs (analytics) of all feature flags or settings.

        :param user: the user object to identify the caller.
        :return: list of variation IDs
        """
        self.log.warning('get_all_variation_ids is deprecated and will be removed in a future major version. '
                         'Please use [get_all_value_details] instead.')

        keys = self.get_all_keys()
        variation_ids = []
        for key in keys:
            variation_id = self.get_variation_id(key, None, user)
            if variation_id is not None:
                variation_ids.append(variation_id)

        return variation_ids

    def get_key_and_value(self, variation_id):
        """
        Gets the key of a setting, and it's value identified by the given Variation ID (analytics)

        :param variation_id: variation ID
        :return: key and value
        """
        settings, _ = self.__get_settings()
        if settings is None:
            self.log.warning('Evaluating get_key_and_value(\'%s\') failed. Cache is empty. '
                             'Returning None.' % variation_id)
            return None

        for key, value in list(settings.items()):
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
        """
        Evaluates and returns the values of all feature flags and settings.

        :param user: the user object to identify the caller.
        :return: dictionary of values
        """
        keys = self.get_all_keys()
        all_values = {}
        for key in keys:
            value = self.get_value(key, None, user)
            if value is not None:
                all_values[key] = value

        return all_values

    def get_all_value_details(self, user=None):
        """
        Gets the values along with evaluation details of all feature flags and settings.

        :param user: the user object to identify the caller.
        :return: list of all evaluation details
        """
        settings, fetch_time = self.__get_settings()
        if settings is None:
            message = 'Evaluating get_all_value_details() failed. Cache is empty. Returning empty list.'
            self.log.error(message)
            return []

        details_result = []
        for key, value in list(settings.items()):
            details = self.__evaluate(key=key,
                                      user=user,
                                      default_value=None,
                                      default_variation_id=None,
                                      settings=settings,
                                      fetch_time=fetch_time)
            details_result.append(details)

        return details_result

    def force_refresh(self):
        """
        Initiates a force refresh on the cached configuration.

        :return: RefreshResult object
        """
        if self._config_service:
            return self._config_service.refresh()

        return RefreshResult(False,
                             'The SDK uses the LocalOnly flag override behavior which prevents making HTTP requests.')

    def set_default_user(self, user):
        """
        Sets the default user.

        :param user: the user object to identify the caller.
        """
        self._default_user = user

    def clear_default_user(self):
        """
        Sets the default user to None.
        """
        self._default_user = None

    def set_online(self):
        """
        Configures the SDK to allow HTTP requests.
        """
        if self._config_service:
            self._config_service.set_online()

        self.log.debug('Switched to ONLINE mode.')

    def set_offline(self):
        """
        Configures the SDK to not initiate HTTP requests and work only from its cache.
        """
        if self._config_service:
            self._config_service.set_offline()

        self.log.debug('Switched to OFFLINE mode.')

    def is_offline(self):
        """
        True when the SDK is configured not to initiate HTTP requests, otherwise false.
        """
        if self._config_service:
            return self._config_service.is_offline()

        return True

    def get_hooks(self):
        """
        Gets the Hooks object for subscribing events.

        :return: Hooks object
        """
        return self._hooks

    def close(self):
        """
        Closes the underlying resources.
        """
        with ConfigCatClient._lock:
            self.__close_resources()
            ConfigCatClient._instances.pop(self._sdk_key)

    def __close_resources(self):
        if self._config_service:
            self._config_service.close()
        self._hooks.clear()

    def __get_settings(self):
        if self._override_data_source:
            behaviour = self._override_data_source.get_behaviour()

            if behaviour == OverrideBehaviour.LocalOnly:
                return self._override_data_source.get_overrides(), utils.distant_past
            elif behaviour == OverrideBehaviour.RemoteOverLocal:
                remote_settings, fetch_time = self._config_service.get_settings()
                local_settings = self._override_data_source.get_overrides()
                if not remote_settings:
                    remote_settings = {}
                if not local_settings:
                    local_settings = {}
                result = copy.deepcopy(local_settings)
                if result:
                    result.update(remote_settings)
                return result, fetch_time
            elif behaviour == OverrideBehaviour.LocalOverRemote:
                remote_settings, fetch_time = self._config_service.get_settings()
                local_settings = self._override_data_source.get_overrides()
                if not remote_settings:
                    remote_settings = {}
                if not local_settings:
                    local_settings = {}
                result = copy.deepcopy(remote_settings)
                result.update(local_settings)
                return result, fetch_time

        return self._config_service.get_settings()

    def __get_cache_key(self):
        return hashlib.sha1(('python_' + CONFIG_FILE_NAME + '_' + self._sdk_key).encode('utf-8')).hexdigest()

    def __evaluate(self, key, user, default_value, default_variation_id, settings, fetch_time):
        user = user if user is not None else self._default_user
        value, variation_id, rule, percentage_rule, error = self._rollout_evaluator.evaluate(
            key=key,
            user=user,
            default_value=default_value,
            default_variation_id=default_variation_id,
            settings=settings)

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
