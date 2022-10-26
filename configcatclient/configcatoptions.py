from .datagovernance import DataGovernance
from .pollingmode import PollingMode


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
                 default_user=None):
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
