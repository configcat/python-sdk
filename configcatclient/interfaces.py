from abc import ABCMeta, abstractmethod
from enum import Enum


class ConfigFetcher(object):
    """
        Config fetcher interface
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_configuration_json(self):
        """
        :return: Returns the configuration json Dictionary
        """

    @abstractmethod
    def close(self):
        """
            Closes the ConfigFetcher's resources
        """


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


class LogLevel(Enum):
    OFF = 0
    ERROR = 1
    WARNING = 2
    INFO = 3

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class ConfigCatLogger(object):
    """
        Logger interface
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.log_level = LogLevel.WARNING

    def set_log_level(self, log_level: LogLevel):
        self.log_level = log_level

    @abstractmethod
    def info(self, message):
        """

        :param message:
        :return:
        """

    @abstractmethod
    def warning(self, message):
        """

        :param message:
        :return:
        """

    @abstractmethod
    def error(self, message):
        """

        :param message:
        :return:
        """


class ConfigCatClientException(Exception):
    """
    Generic ConfigCatClientException
    """
