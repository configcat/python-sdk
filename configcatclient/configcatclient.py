import logging
import sys
from threading import Lock

from . import utils
from .configservice import ConfigService
from .config import TARGETING_RULES, VARIATION_ID, PERCENTAGE_OPTIONS, FEATURE_FLAGS, SERVED_VALUE, SETTING_TYPE
from .evaluationdetails import EvaluationDetails
from .evaluationlogbuilder import EvaluationLogBuilder
from .interfaces import ConfigCatClientException
from .logger import Logger
from .configfetcher import ConfigFetcher
from .configcache import NullConfigCache
from .configcatoptions import ConfigCatOptions, Hooks
from .overridedatasource import OverrideBehaviour
from .refreshresult import RefreshResult
from .rolloutevaluator import RolloutEvaluator, get_value
from collections import namedtuple
import copy
from .utils import method_is_called_from, get_date_time
import re

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
                    client.log.warning('There is an existing client instance for the specified SDK Key. '
                                       'No new client instance will be created and the specified options are ignored. '
                                       'Returning the existing client instance. SDK Key: \'%s\'.',
                                       sdk_key, event_id=3000)
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
                value._close_resources()
            cls._instances.clear()

    def __init__(self,
                 sdk_key,
                 options=ConfigCatOptions()):

        self._hooks = options.hooks if options.hooks is not None else Hooks()
        self.log = Logger('configcat', self._hooks)

        if not method_is_called_from(ConfigCatClient.get):
            raise ConfigCatClientException('ConfigCatClient.__init__() is private. Create the ConfigCat Client as a '
                                           'Singleton object with `ConfigCatClient.get()` instead.')

        if sdk_key is None:
            raise ConfigCatClientException('SDK Key is required.')

        if options.flag_overrides:
            self._override_data_source = options.flag_overrides.create_data_source(self.log)
        else:
            self._override_data_source = None

        # In case of local only flag overrides mode, we accept any SDK Key format.
        if self._override_data_source is None or self._override_data_source.get_behaviour() != OverrideBehaviour.LocalOnly:
            is_valid_sdk_key = re.match('^.{22}/.{22}$', sdk_key) is not None or \
                re.match('^configcat-sdk-1/.{22}/.{22}$', sdk_key) is not None or \
                (options.base_url and re.match('^configcat-proxy/.+$', sdk_key) is not None)
            if not is_valid_sdk_key:
                raise ConfigCatClientException('SDK Key `%s` is invalid.' % sdk_key)

        self._sdk_key = sdk_key
        self._default_user = options.default_user
        self._rollout_evaluator = RolloutEvaluator(self.log)
        config_cache = options.config_cache if options.config_cache is not None else NullConfigCache()

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
                                                 config_cache,
                                                 options.offline)

    def get_value(self, key, default_value, user=None):
        """
        Gets the value of a feature flag or setting identified by the given `key`.

        :param key: the identifier of the feature flag or setting.
        :param default_value: in case of any failure, this value will be returned.
        :param user: the user object to identify the caller.
        :return: the value.
        """
        config, fetch_time = self._get_config()
        if config is None or config.get(FEATURE_FLAGS) is None:
            message = 'Config JSON is not present when evaluating setting \'%s\'. ' \
                      'Returning the `%s` parameter that you specified in your application: \'%s\'.'
            message_args = (key, 'default_value', str(default_value))
            self.log.error(message, *message_args, event_id=1000)
            self._hooks.invoke_on_flag_evaluated(
                EvaluationDetails.from_error(key, default_value, Logger.format(message, message_args)))
            return default_value

        details = self._evaluate(key=key,
                                 user=user,
                                 default_value=default_value,
                                 default_variation_id=None,
                                 config=config,
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
        config, fetch_time = self._get_config()
        if config is None or config.get(FEATURE_FLAGS) is None:
            message = 'Config JSON is not present when evaluating setting \'%s\'. ' \
                      'Returning the `%s` parameter that you specified in your application: \'%s\'.'
            message_args = (key, 'default_value', str(default_value))
            self.log.error(message, *message_args, event_id=1000)
            details = EvaluationDetails.from_error(key, default_value, Logger.format(message, message_args))
            self._hooks.invoke_on_flag_evaluated(details)
            return details

        details = self._evaluate(key=key,
                                 user=user,
                                 default_value=default_value,
                                 default_variation_id=None,
                                 config=config,
                                 fetch_time=fetch_time)

        return details

    def get_all_keys(self):
        """
        Gets all setting keys.

        :return: list of keys.
        """
        config, _ = self._get_config()
        if config is None:
            self.log.error('Config JSON is not present. Returning %s.', 'empty list', event_id=1000)
            return []

        settings = config.get(FEATURE_FLAGS, {})
        return list(settings)

    def get_key_and_value(self, variation_id):
        """
        Gets the key of a setting, and it's value identified by the given Variation ID (analytics)

        :param variation_id: variation ID
        :return: key and value
        """
        config, _ = self._get_config()
        if config is None:
            self.log.error('Config JSON is not present. Returning %s.', 'None', event_id=1000)
            return None

        settings = config.get(FEATURE_FLAGS, {})
        try:
            for key, value in list(settings.items()):
                setting_type = value.get(SETTING_TYPE)
                if variation_id == value.get(VARIATION_ID):
                    return KeyValue(key, get_value(value, setting_type))

                targeting_rules = value.get(TARGETING_RULES, [])
                for targeting_rule in targeting_rules:
                    served_value = targeting_rule.get(SERVED_VALUE)
                    if served_value is not None and variation_id == served_value.get(VARIATION_ID):
                        return KeyValue(key, get_value(served_value, setting_type))

                    rollout_percentage_items = targeting_rule.get(PERCENTAGE_OPTIONS, [])
                    for rollout_percentage_item in rollout_percentage_items:
                        if variation_id == rollout_percentage_item.get(VARIATION_ID):
                            return KeyValue(key, get_value(rollout_percentage_item, setting_type))
        except Exception:
            self.log.exception('Error occurred in the `' + __name__ + '` method. Returning None.', event_id=1002)
            return None

        self.log.error('Could not find the setting for the specified variation ID: \'%s\'.', variation_id, event_id=2011)
        return None

    def get_all_values(self, user=None):
        """
        Evaluates and returns the values of all feature flags and settings.

        :param user: the user object to identify the caller.
        :return: dictionary of values
        """
        config, _ = self._get_config()
        if config is None:
            self.log.error('Config JSON is not present. Returning %s.', 'empty dictionary', event_id=1000)
            return {}

        settings = config.get(FEATURE_FLAGS, {})
        all_values = {}
        for key in list(settings):
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
        config, fetch_time = self._get_config()
        if config is None:
            self.log.error('Config JSON is not present. Returning %s.', 'empty list', event_id=1000)
            return []

        details_result = []
        settings = config.get(FEATURE_FLAGS, {})
        for key in list(settings):
            details = self._evaluate(key=key,
                                     user=user,
                                     default_value=None,
                                     default_variation_id=None,
                                     config=config,
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
        else:
            self.log.warning('Client is configured to use the `%s` override behavior, thus `%s()` has no effect.',
                             'LocalOnly', 'set_online', event_id=3202)

    def set_offline(self):
        """
        Configures the SDK to not initiate HTTP requests and work only from its cache.
        """
        if self._config_service:
            self._config_service.set_offline()

    def is_offline(self):
        """
        True when the SDK is configured not to initiate HTTP requests, otherwise False.
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
            self._close_resources()
            ConfigCatClient._instances.pop(self._sdk_key)

    def _close_resources(self):
        if self._config_service:
            self._config_service.close()
        self._hooks.clear()

    def _get_config(self):
        if self._override_data_source:
            behaviour = self._override_data_source.get_behaviour()

            if behaviour == OverrideBehaviour.LocalOnly:
                return self._override_data_source.get_overrides(), utils.distant_past
            elif behaviour == OverrideBehaviour.RemoteOverLocal:
                remote_config, fetch_time = self._config_service.get_config()
                local_config = self._override_data_source.get_overrides()
                if not remote_config:
                    remote_config = {FEATURE_FLAGS: {}}
                if not local_config:
                    local_config = {FEATURE_FLAGS: {}}
                result = copy.deepcopy(local_config)
                result[FEATURE_FLAGS].update(remote_config[FEATURE_FLAGS])
                return result, fetch_time
            elif behaviour == OverrideBehaviour.LocalOverRemote:
                remote_config, fetch_time = self._config_service.get_config()
                local_config = self._override_data_source.get_overrides()
                if not remote_config:
                    remote_config = {FEATURE_FLAGS: {}}
                if not local_config:
                    local_config = {FEATURE_FLAGS: {}}
                result = copy.deepcopy(remote_config)
                result[FEATURE_FLAGS].update(local_config[FEATURE_FLAGS])
                return result, fetch_time

        return self._config_service.get_config()

    def _check_type_missmatch(self, value, default_value):
        is_float_int_missmatch = \
            (type(value) is float and type(default_value) is int) or \
            (type(value) is int and type(default_value) is float)

        # On Python 2.7, do not log a warning if the type missmatch is between str and unicode.
        # (ignore warning: unicode is undefined in Python 3)
        is_str_unicode_missmatch = \
            (sys.version_info[0] == 2 and type(value) is unicode and type(default_value) is str) or \
            (sys.version_info[0] == 2 and type(value) is str and type(default_value) is unicode)  # noqa: F821

        if default_value is not None and type(value) is not type(default_value):
            if not is_float_int_missmatch and not is_str_unicode_missmatch:
                self.log.warning("The type of a setting does not match the type of the specified default value (%s). "
                                 "Setting's type was %s but the default value's type was %s. "
                                 "Please make sure that using a default value not matching the setting's type was intended." %
                                 (default_value, type(value), type(default_value)), event_id=4002)

    def _evaluate(self, key, user, default_value, default_variation_id, config, fetch_time):
        user = user if user is not None else self._default_user

        # Skip building the evaluation log if it won't be logged.
        log_builder = EvaluationLogBuilder() if self.log.isEnabledFor(logging.INFO) else None

        value, variation_id, rule, percentage_rule, error = self._rollout_evaluator.evaluate(
            key=key,
            user=user,
            default_value=default_value,
            default_variation_id=default_variation_id,
            config=config,
            log_builder=log_builder)

        self._check_type_missmatch(value, default_value)

        if log_builder:
            self.log.info(str(log_builder), event_id=5000)

        details = EvaluationDetails(key=key,
                                    value=value,
                                    variation_id=variation_id,
                                    fetch_time=get_date_time(fetch_time) if fetch_time is not None else None,
                                    user=user,
                                    is_default_value=True if error else False,
                                    error=error,
                                    matched_targeting_rule=rule,
                                    matched_percentage_option=percentage_rule)
        self._hooks.invoke_on_flag_evaluated(details)
        return details
