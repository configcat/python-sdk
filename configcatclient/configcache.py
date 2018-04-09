from .interfaces import ConfigCache


class InMemoryConfigCache(ConfigCache):

    def __init__(self):
        self._value = None

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
