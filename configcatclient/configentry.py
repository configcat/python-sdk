import json

from . import utils


class ConfigEntry(object):
    CONFIG = 'config'
    ETAG = 'etag'
    FETCH_TIME = 'fetch_time'

    def __init__(self, config={}, etag='', fetch_time=utils.distant_past):
        self.config = config
        self.etag = etag
        self.fetch_time = fetch_time

    def is_empty(self):
        return self == ConfigEntry.empty

    def serialize(self):
        return '{:.7f}\n{}\n{}'.format(self.fetch_time, self.etag, json.dumps(self.config))

    @classmethod
    def create_from_string(cls, string):
        if not string:
            return ConfigEntry.empty

        fetch_time_index = string.find('\n')
        etag_index = string.find('\n', fetch_time_index + 1)
        if fetch_time_index < 0 or etag_index < 0:
            raise ValueError('Number of values is fewer than expected.')

        try:
            fetch_time = float(string[0:fetch_time_index])
        except ValueError:
            raise ValueError('Invalid fetch time: {}'.format(string[0:fetch_time_index]))

        etag = string[fetch_time_index + 1:etag_index]
        if not etag:
            raise ValueError('Empty eTag value')
        try:
            config_json = string[etag_index + 1:]
            config = json.loads(config_json)
        except ValueError as e:
            raise ValueError('Invalid config JSON: {}. {}'.format(config_json, str(e)))

        return ConfigEntry(config=config, etag=etag, fetch_time=fetch_time)


ConfigEntry.empty = ConfigEntry(etag='empty')
