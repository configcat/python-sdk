from .interfaces import ConfigCache


class NullConfigCache(ConfigCache):

    def __init__(self):
        self._value = {}

    def get(self, key):
        return None

    def set(self, key, value):
        pass  # do nothing


class InMemoryConfigCache(ConfigCache):

    def __init__(self):
        self._value = {}

    def get(self, key):
        return self._value.get(key)

    def set(self, key, value):
        self._value[key] = value
