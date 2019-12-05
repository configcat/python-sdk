from .configcatclient import ConfigCatClient
from .interfaces import ConfigCatClientException


def create_client(api_key):
    """
    Create an instance of ConfigCatClient and setup Auto Poll mode with default options

    :param api_key: ConfigCat ApiKey to access your configuration.
    """
    return create_client_with_auto_poll(api_key)


def create_client_with_auto_poll(api_key, poll_interval_seconds=60, max_init_wait_time_seconds=5,
                                 on_configuration_changed_callback=None, config_cache_class=None,
                                 base_url=None, proxies=None, proxy_auth=None):
    """
    Create an instance of ConfigCatClient and setup Auto Poll mode with custom options

    :param api_key: ConfigCat ApiKey to access your configuration.
    :param poll_interval_seconds: The client's poll interval in seconds. Default: 60 seconds.
    :param on_configuration_changed_callback: You can subscribe to configuration changes with this callback
    :param max_init_wait_time_seconds: maximum waiting time for first configuration fetch in polling mode.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { 'https': 'your_proxy_ip:your_proxy_port' }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    """

    if api_key is None:
        raise ConfigCatClientException('API Key is required.')

    if poll_interval_seconds < 1:
        poll_interval_seconds = 1

    if max_init_wait_time_seconds < 0:
        max_init_wait_time_seconds = 0

    return ConfigCatClient(api_key, poll_interval_seconds, max_init_wait_time_seconds,
                           on_configuration_changed_callback, 0, config_cache_class, base_url, proxies, proxy_auth)


def create_client_with_lazy_load(api_key, cache_time_to_live_seconds=60, config_cache_class=None,
                                 base_url=None, proxies=None, proxy_auth=None):
    """
    Create an instance of ConfigCatClient and setup Lazy Load mode with custom options

    :param api_key: ConfigCat ApiKey to access your configuration.
    :param cache_time_to_live_seconds: The cache TTL.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    """

    if api_key is None:
        raise ConfigCatClientException('API Key is required.')

    if cache_time_to_live_seconds < 1:
        cache_time_to_live_seconds = 1

    return ConfigCatClient(api_key, 0, 0, None, cache_time_to_live_seconds, config_cache_class, base_url,
                           proxies, proxy_auth)


def create_client_with_manual_poll(api_key, config_cache_class=None,
                                   base_url=None, proxies=None, proxy_auth=None):
    """
    Create an instance of ConfigCatClient and setup Manual Poll mode with custom options

    :param api_key: ConfigCat ApiKey to access your configuration.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    :param base_url: You can set a base_url if you want to use a proxy server between your application and ConfigCat
    :param proxies: Proxy addresses. e.g. { "https": "your_proxy_ip:your_proxy_port" }
    :param proxy_auth: Proxy authentication. e.g. HTTPProxyAuth('username', 'password')
    """

    if api_key is None:
        raise ConfigCatClientException('API Key is required.')

    return ConfigCatClient(api_key, 0, 0, None, 0, config_cache_class, base_url, proxies, proxy_auth)
