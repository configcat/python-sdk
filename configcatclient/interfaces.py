from abc import ABCMeta, abstractmethod


class ConfigCache(object):
    """
        Config cache interface
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self):
        """
        :returns the config json object from the cache
        """

    @abstractmethod
    def set(self, value):
        """
        Sets the config json cache.
        """


class CachePolicy(object):
    """
        Config cache interface
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self):
        """
        :returns the config json object from the cache
        """

    @abstractmethod
    def force_refresh(self):
        """

        :return:
        """

    @abstractmethod
    def stop(self):
        """

        :return:
        """


class ConfigCatClientException(Exception):
    """
    Generic ConfigCatClientException
    """
