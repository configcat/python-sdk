from abc import ABCMeta, abstractmethod


class ConfigCache(object):
    """
    Config cache interface
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, key):
        """
        :return: the config json object from the cache
        """

    @abstractmethod
    def set(self, key, value):
        """
        Sets the config json cache.
        """


class ConfigCatClientException(Exception):
    """
    Generic ConfigCatClientException
    """
