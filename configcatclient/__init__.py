from .configcatclient import ConfigCatClient
from .interfaces import ConfigCatClientException
from .datagovernance import DataGovernance
from .configcatoptions import ConfigCatOptions
from .pollingmode import PollingMode


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
                                 on_configuration_changed_callback=None,
                                 config_cache=None,
                                 base_url=None, proxies=None, proxy_auth=None,
                                 connect_timeout_seconds=10, read_timeout_seconds=30,
                                 flag_overrides=None,
                                 data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Auto Poll mode with custom options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param poll_interval_seconds: The client's poll interval in seconds. Default: 60 seconds.
    :param max_init_wait_time_seconds: maximum waiting time for first configuration fetch.
    :param on_configuration_changed_callback: You can subscribe to configuration changes with this callback
    :param config_cache: If you want to use custom caching instead of the client's default,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { 'https': 'your_proxy_ip:your_proxy_port' }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    :param connect_timeout_seconds: The number of seconds to wait for the server to make the initial connection
    (i.e. completing the TCP connection handshake). Default: 10 seconds.
    :param read_timeout_seconds: The number of seconds to wait for the server to respond before giving up. Default: 30 seconds.
    :param flag_overrides: An FlagOverrides implementation used to override feature flags & settings.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """

    options = ConfigCatOptions(
        base_url=base_url,
        polling_mode=PollingMode.auto_poll(auto_poll_interval_seconds=poll_interval_seconds,
                                           max_init_wait_time_seconds=max_init_wait_time_seconds),
        config_cache=config_cache,
        proxies=proxies,
        proxy_auth=proxy_auth,
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
        flag_overrides=flag_overrides,
        data_governance=data_governance)
    client = ConfigCatClient.get(sdk_key=sdk_key, options=options)

    if on_configuration_changed_callback is not None:
        client.get_hooks().add_on_config_changed(on_configuration_changed_callback)

    client.log.warning('create_client_with_auto_poll is deprecated. '
                       'Create the ConfigCat Client as a Singleton object with `ConfigCatClient.get()` instead')
    return client


def create_client_with_lazy_load(sdk_key, cache_time_to_live_seconds=60, config_cache=None,
                                 base_url=None, proxies=None, proxy_auth=None,
                                 connect_timeout_seconds=10, read_timeout_seconds=30,
                                 flag_overrides=None,
                                 data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Lazy Load mode with custom options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param cache_time_to_live_seconds: The cache TTL.
    :param config_cache: If you want to use custom caching instead of the client's default,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    :param connect_timeout_seconds: The number of seconds to wait for the server to make the initial connection
    (i.e. completing the TCP connection handshake). Default: 10 seconds.
    :param read_timeout_seconds: The number of seconds to wait for the server to respond before giving up. Default: 30 seconds.
    :param flag_overrides: An FlagOverrides implementation used to override feature flags & settings.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """

    options = ConfigCatOptions(
        base_url=base_url,
        polling_mode=PollingMode.lazy_load(cache_refresh_interval_seconds=cache_time_to_live_seconds),
        config_cache=config_cache,
        proxies=proxies,
        proxy_auth=proxy_auth,
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
        flag_overrides=flag_overrides,
        data_governance=data_governance)
    client = ConfigCatClient.get(sdk_key=sdk_key, options=options)
    client.log.warning('create_client_with_lazy_load is deprecated. '
                       'Create the ConfigCat Client as a Singleton object with `ConfigCatClient.get()` instead')
    return client


def create_client_with_manual_poll(sdk_key, config_cache=None,
                                   base_url=None, proxies=None, proxy_auth=None,
                                   connect_timeout_seconds=10, read_timeout_seconds=30,
                                   flag_overrides=None,
                                   data_governance=DataGovernance.Global):
    """
    Create an instance of ConfigCatClient and setup Manual Poll mode with custom options

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param config_cache: If you want to use custom caching instead of the client's default,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    :param connect_timeout_seconds: The number of seconds to wait for the server to make the initial connection
    (i.e. completing the TCP connection handshake). Default: 10 seconds.
    :param read_timeout_seconds: The number of seconds to wait for the server to respond before giving up. Default: 30 seconds.
    :param flag_overrides: An FlagOverrides implementation used to override feature flags & settings.
    :param data_governance:
    Default: Global. Set this parameter to be in sync with the Data Governance preference on the Dashboard: \n
    https://app.configcat.com/organization/data-governance \n
    (Only Organization Admins have access)
    """

    options = ConfigCatOptions(
        base_url=base_url,
        polling_mode=PollingMode.manual_poll(),
        config_cache=config_cache,
        proxies=proxies,
        proxy_auth=proxy_auth,
        connect_timeout_seconds=connect_timeout_seconds,
        read_timeout_seconds=read_timeout_seconds,
        flag_overrides=flag_overrides,
        data_governance=data_governance)
    client = ConfigCatClient.get(sdk_key=sdk_key, options=options)
    client.log.warning('create_client_with_manual_poll is deprecated. '
                       'Create the ConfigCat Client as a Singleton object with `ConfigCatClient.get()` instead')
    return client
