from .configcatclient import ConfigCatClient
from .interfaces import ConfigCatClientException
from .datagovernance import DataGovernance


def create_client(sdk_key, data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Auto Poll mode with default options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """
    return create_client_with_auto_poll(sdk_key, data_governance=data_governance)


def create_client_with_auto_poll(sdk_key, poll_interval_seconds=60, max_init_wait_time_seconds=5,
                                 on_configuration_changed_callback=None, config_cache_class=None,
                                 base_url=None, proxies=None, proxy_auth=None, connect_timeout=10, read_timeout=30,
                                 flag_overrides=None,
                                 data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Auto Poll mode with custom options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param poll_interval_seconds: The client's poll interval in seconds. Default: 60 seconds.
    :param on_configuration_changed_callback: You can subscribe to configuration changes with this callback
    :param max_init_wait_time_seconds: maximum waiting time for first configuration fetch.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { 'https': 'your_proxy_ip:your_proxy_port' }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    :param connect_timeout: The number of seconds to wait for the server to make the initial connection
    (i.e. completing the TCP connection handshake). Default: 10 seconds.
    :param read_timeout: The number of seconds to wait for the server to respond before giving up. Default: 30 seconds.
    :param flag_overrides: An OverrideDataSource implementation used to override feature flags & settings.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """

    if sdk_key is None:
        raise ConfigCatClientException('SDK Key is required.')

    if poll_interval_seconds < 1:
        poll_interval_seconds = 1

    if max_init_wait_time_seconds < 0:
        max_init_wait_time_seconds = 0

    return ConfigCatClient(sdk_key=sdk_key,
                           poll_interval_seconds=poll_interval_seconds,
                           max_init_wait_time_seconds=max_init_wait_time_seconds,
                           on_configuration_changed_callback=on_configuration_changed_callback,
                           cache_time_to_live_seconds=0,
                           config_cache_class=config_cache_class,
                           base_url=base_url,
                           proxies=proxies,
                           proxy_auth=proxy_auth,
                           connect_timeout=connect_timeout,
                           read_timeout=read_timeout,
                           flag_overrides=flag_overrides,
                           data_governance=data_governance)


def create_client_with_lazy_load(sdk_key, cache_time_to_live_seconds=60, config_cache_class=None,
                                 base_url=None, proxies=None, proxy_auth=None, connect_timeout=10, read_timeout=30,
                                 flag_overrides=None,
                                 data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Lazy Load mode with custom options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param cache_time_to_live_seconds: The cache TTL.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    :param connect_timeout: The number of seconds to wait for the server to make the initial connection
    (i.e. completing the TCP connection handshake). Default: 10 seconds.
    :param read_timeout: The number of seconds to wait for the server to respond before giving up. Default: 30 seconds.
    :param flag_overrides: An OverrideDataSource implementation used to override feature flags & settings.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """

    if sdk_key is None:
        raise ConfigCatClientException('SDK Key is required.')

    if cache_time_to_live_seconds < 1:
        cache_time_to_live_seconds = 1

    return ConfigCatClient(sdk_key=sdk_key,
                           poll_interval_seconds=0,
                           max_init_wait_time_seconds=0,
                           on_configuration_changed_callback=None,
                           cache_time_to_live_seconds=cache_time_to_live_seconds,
                           config_cache_class=config_cache_class,
                           base_url=base_url,
                           proxies=proxies,
                           proxy_auth=proxy_auth,
                           connect_timeout=connect_timeout,
                           read_timeout=read_timeout,
                           flag_overrides=flag_overrides,
                           data_governance=data_governance)


def create_client_with_manual_poll(sdk_key, config_cache_class=None,
                                   base_url=None, proxies=None, proxy_auth=None, connect_timeout=10, read_timeout=30,
                                   flag_overrides=None,
                                   data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Manual Poll mode with custom options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    :param connect_timeout: The number of seconds to wait for the server to make the initial connection
    (i.e. completing the TCP connection handshake). Default: 10 seconds.
    :param read_timeout: The number of seconds to wait for the server to respond before giving up. Default: 30 seconds.
    :param flag_overrides: An OverrideDataSource implementation used to override feature flags & settings.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """

    if sdk_key is None:
        raise ConfigCatClientException('SDK Key is required.')

    return ConfigCatClient(sdk_key=sdk_key,
                           poll_interval_seconds=0,
                           max_init_wait_time_seconds=0,
                           on_configuration_changed_callback=None,
                           cache_time_to_live_seconds=0,
                           config_cache_class=config_cache_class,
                           base_url=base_url,
                           proxies=proxies,
                           proxy_auth=proxy_auth,
                           connect_timeout=connect_timeout,
                           read_timeout=read_timeout,
                           flag_overrides=flag_overrides,
                           data_governance=data_governance)
