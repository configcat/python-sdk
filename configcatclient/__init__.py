from .configcatclient import ConfigCatClient
from .interfaces import ConfigCatClientException
from .readwritelock import ReadWriteLock

__client = None
__lock = ReadWriteLock()


def initialize(api_key,
               poll_interval_seconds=60,
               max_init_wait_time_seconds=5,
               on_configuration_changed_callback=None,
               config_cache_class=None):
    """
    Initializes the ConfigCatClient. If the client is already initialized initialize does nothing.

    :param api_key: The API Key.
    :param poll_interval_seconds: The client's polls interval in seconds.
    :param on_configuration_changed_callback: You can subscribe to configuration changes with this callback
    :param max_init_wait_time_seconds: maximum waiting time for first configuration fetch in polling mode.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    """
    global __client
    global __lock

    if api_key is None:
        raise ConfigCatClientException('API Key is required.')

    if __client is not None:
        return

    try:
        __lock.acquire_write()

        if __client is not None:
            return

        if poll_interval_seconds < 1:
            poll_interval_seconds = 1

        if max_init_wait_time_seconds < 0:
            max_init_wait_time_seconds = 0

        __client = ConfigCatClient(api_key, poll_interval_seconds, max_init_wait_time_seconds,
                                   on_configuration_changed_callback, 0, config_cache_class)
    finally:
        __lock.release_write()


def initialize_lazy_loading(api_key,
                            cache_time_to_live_seconds=60,
                            config_cache_class=None):
    """
    Initializes the ConfigCatClient. If the client is already initialized initialize does nothing.

    :param api_key: The API Key.
    :param cache_time_to_live_seconds: The cache TTL.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    """
    global __client
    global __lock

    if api_key is None:
        raise ConfigCatClientException('API Key is required.')

    if __client is not None:
        return

    try:
        __lock.acquire_write()

        if __client is not None:
            return

        if cache_time_to_live_seconds < 1:
            cache_time_to_live_seconds = 1

        __client = ConfigCatClient(api_key, 0, 0, None,
                                   cache_time_to_live_seconds, config_cache_class)
    finally:
        __lock.release_write()


def initialize_manual_polling(api_key, config_cache_class=None):
    """
    Initializes the ConfigCatClient. If the client is already initialized initialize does nothing.

    :param api_key: The API Key.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    """
    global __client
    global __lock

    if api_key is None:
        raise ConfigCatClientException('API Key is required.')

    if __client is not None:
        return

    try:
        __lock.acquire_write()

        if __client is not None:
            return

        __client = ConfigCatClient(api_key, 0, 0, None, 0, config_cache_class)
    finally:
        __lock.release_write()


def get():
    """
    Gets the initialized ConfigCatClient.
    In case you haven't called initialize before it raises a ConfigCatClientException.
    :return: The initialized ConfigCatClient.
    """
    global __client
    global __lock

    try:
        __lock.acquire_read()
        if __client is not None:
            return __client
    finally:
        __lock.release_read()

    raise ConfigCatClientException("Initialize should be called before using ConfigCatClient")


def stop():
    """
    Closes all resources
    """
    global __client
    global __lock

    try:
        __lock.acquire_write()

        if __client is not None:
            __client.stop()

        __client = None
    finally:
        __lock.release_write()
