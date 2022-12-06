import logging
from .datagovernance import DataGovernance
from .pollingmode import PollingMode


class Hooks(object):
    """
    Events fired by [ConfigCatClient].
    """

    def __init__(self, on_ready_callback=None, on_config_changed_callback=None,
                 on_flag_evaluated_callback=None, on_error_callback=None):
        self._on_ready_callbacks = [on_ready_callback] if on_ready_callback else []
        self._on_config_changed_callbacks = [on_config_changed_callback] if on_config_changed_callback else []
        self._on_flag_evaluated_callbacks = [on_flag_evaluated_callback] if on_flag_evaluated_callback else []
        self._on_error_callbacks = [on_error_callback] if on_error_callback else []

    def add_on_ready(self, callback):
        self._on_ready_callbacks.append(callback)

    def add_on_config_changed(self, callback):
        self._on_config_changed_callbacks.append(callback)

    def add_on_flag_evaluated(self, callback):
        self._on_flag_evaluated_callbacks.append(callback)

    def add_on_error(self, callback):
        self._on_error_callbacks.append(callback)

    def invoke_on_ready(self):
        for callback in self._on_ready_callbacks:
            try:
                callback()
            except Exception as e:
                error = 'Exception occurred during invoke_on_ready callback: ' + str(e)
                self.invoke_on_error(error)
                logging.error(error)

    def invoke_on_config_changed(self, config):
        for callback in self._on_config_changed_callbacks:
            try:
                callback(config)
            except Exception as e:
                error = 'Exception occurred during invoke_on_config_changed callback: ' + str(e)
                self.invoke_on_error(error)
                logging.error(error)

    def invoke_on_flag_evaluated(self, evaluation_details):
        for callback in self._on_flag_evaluated_callbacks:
            try:
                callback(evaluation_details)
            except Exception as e:
                error = 'Exception occurred during invoke_on_flag_evaluated callback: ' + str(e)
                self.invoke_on_error(error)
                logging.error(error)

    def invoke_on_error(self, error):
        for callback in self._on_error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logging.error('Exception occurred during invoke_on_error callback: ' + str(e))

    def clear(self):
        self._on_ready_callbacks[:] = []
        self._on_config_changed_callbacks[:] = []
        self._on_flag_evaluated_callbacks[:] = []
        self._on_error_callbacks[:] = []


class ConfigCatOptions(object):
    """
    Configuration options for ConfigCatClient.
    """

    def __init__(self,
                 base_url=None,
                 polling_mode=PollingMode.auto_poll(),
                 config_cache=None,
                 proxies=None,
                 proxy_auth=None,
                 connect_timeout_seconds=10,
                 read_timeout_seconds=30,
                 flag_overrides=None,
                 data_governance=DataGovernance.Global,
                 default_user=None,
                 hooks=None,
                 offline=False):
        """
        Default: `DataGovernance.Global`. Set this parameter to be in sync with the
        Data Governance preference on the [Dashboard](https://app.configcat.com/organization/data-governance).
        (Only Organization Admins have access)
        """
        self.data_governance = data_governance

        # The base ConfigCat CDN url.
        self.base_url = base_url

        # The polling mode.
        self.polling_mode = polling_mode

        # The cache implementation used to cache the downloaded config.json.
        self.config_cache = config_cache

        # Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
        self.proxies = proxies

        # Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
        self.proxy_auth = proxy_auth

        # The number of seconds to wait for the server to make the initial connection
        self.connect_timeout_seconds = connect_timeout_seconds

        # The number of seconds to wait for the server to respond before giving up.
        self.read_timeout_seconds = read_timeout_seconds

        # Feature flag and setting overrides.
        self.flag_overrides = flag_overrides

        # The default user, used as fallback when there's no user parameter is passed to the getValue() method.
        self.default_user = default_user

        # Hooks for events sent by ConfigCatClient.
        self.hooks = hooks

        # Indicates whether the SDK should be initialized in offline mode or not.
        self.offline = offline
