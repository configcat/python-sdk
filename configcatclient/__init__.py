from .configcatclient import ConfigCatClient
from .interfaces import ConfigCatClientException
from .readwritelock import ReadWriteLock

__client = None
__lock = ReadWriteLock()


def initialize(project_secret,
               poll_interval_seconds=60,
               max_init_wait_time_seconds=5,
               on_configuration_changed_callback=None,
               config_cache_class=None):
    """
    Initializes the BetterConfigClient. If the client is already initialized initialize does nothing.

    :param project_secret: The Project Secret.
    :param poll_interval_seconds: The client's polls interval in seconds.
    :param on_configuration_changed_callback: You can subscribe to configuration changes with this callback
    :param max_init_wait_time_seconds: maximum waiting time for first configuration fetch in polling mode.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    """
    global __client
    global __lock

    if project_secret is None:
        raise ConfigCatClientException('Project secret is required.')

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

        __client = ConfigCatClient(project_secret, poll_interval_seconds, max_init_wait_time_seconds,
                                   on_configuration_changed_callback, 0, config_cache_class)
    finally:
        __lock.release_write()


def initialize_lazy_loading(project_secret,
                            cache_time_to_live_seconds=60,
                            config_cache_class=None):
    """
    Initializes the BetterConfigClient. If the client is already initialized initialize does nothing.

    :param project_secret: The Project Secret.
    :param cache_time_to_live_seconds: The cache TTL.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    """
    global __client
    global __lock

    if project_secret is None:
        raise ConfigCatClientException('Project secret is required.')

    if __client is not None:
        return

    try:
        __lock.acquire_write()

        if __client is not None:
            return

        if cache_time_to_live_seconds < 1:
            cache_time_to_live_seconds = 1

        __client = ConfigCatClient(project_secret, 0, 0, None,
                                   cache_time_to_live_seconds, config_cache_class)
    finally:
        __lock.release_write()


def initialize_manual_polling(project_secret, config_cache_class=None):
    """
    Initializes the BetterConfigClient. If the client is already initialized initialize does nothing.

    :param project_secret: The Project Secret.
    :param config_cache_class: If you want to use custom caching instead of the client's default InMemoryConfigCache,
    You can provide an implementation of ConfigCache.
    """
    global __client
    global __lock

    if project_secret is None:
        raise ConfigCatClientException('Project secret is required.')

    if __client is not None:
        return

    try:
        __lock.acquire_write()

        if __client is not None:
            return

        __client = ConfigCatClient(project_secret, 0, 0, None, 0, config_cache_class)
    finally:
        __lock.release_write()


def get():
    """
    Gets the initialized BetterConfigClient.
    In case you haven't called initialize before it raises a BetterConfigClientException.
    :return: The initialized BetterConfigClient.
    """
    global __client
    global __lock

    try:
        __lock.acquire_read()
        if __client is not None:
            return __client
    finally:
        __lock.release_read()

    raise ConfigCatClientException("Initialize should be called before using BetterConfigClient")


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
