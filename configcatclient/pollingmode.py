from abc import ABCMeta, abstractmethod


class PollingMode(object):
    """
    Describes a polling mode.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def identifier(self):
        """
        :returns the identifier of polling mode. Used for analytical purposes in HTTP User-Agent headers.
        """

    @staticmethod
    def auto_poll(auto_poll_interval_seconds=60, max_init_wait_time_seconds=5, on_config_changed=None):
        """
        Creates a configured auto polling configuration.

        :param auto_poll_interval_seconds: sets at least how often this policy should fetch the latest configuration and refresh the cache.
        :param max_init_wait_time_seconds: sets the maximum waiting time between initialization and the first config acquisition in seconds.
        :param on_config_changed: sets a configuration changed event handler.
        """

        if auto_poll_interval_seconds < 1:
            auto_poll_interval_seconds = 1

        if max_init_wait_time_seconds < 0:
            max_init_wait_time_seconds = 0

        return AutoPollingMode(auto_poll_interval_seconds=auto_poll_interval_seconds,
                               max_init_wait_time_seconds=max_init_wait_time_seconds,
                               on_config_changed=on_config_changed)

    @staticmethod
    def lazy_load(cache_refresh_interval_seconds=60):
        """
        Creates a configured lazy loading polling configuration.

        :param cache_refresh_interval_seconds: sets how long the cache will store its value before fetching the latest from the network again.
        """

        if cache_refresh_interval_seconds < 1:
            cache_refresh_interval_seconds = 1

        return LazyLoadingMode(cache_refresh_interval_seconds=cache_refresh_interval_seconds)

    @staticmethod
    def manual_poll():
        """
        Creates a configured manual polling configuration.
        """
        return ManualPollingMode()


class AutoPollingMode(PollingMode):
    def __init__(self, auto_poll_interval_seconds, max_init_wait_time_seconds, on_config_changed):
        self.auto_poll_interval_seconds = auto_poll_interval_seconds
        self.max_init_wait_time_seconds = max_init_wait_time_seconds
        self.on_config_changed = on_config_changed

    def identifier(self):
        return "a"


class LazyLoadingMode(PollingMode):
    def __init__(self, cache_refresh_interval_seconds):
        self.cache_refresh_interval_seconds = cache_refresh_interval_seconds

    def identifier(self):
        return "l"


class ManualPollingMode(PollingMode):
    def identifier(self):
        return "m"
