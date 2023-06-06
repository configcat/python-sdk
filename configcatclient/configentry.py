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

        tokens = string.split('\n')
        if len(tokens) < 3:
            raise ValueError('Number of values is fewer than expected.')

        try:
            fetch_time = float(tokens[0])
        except ValueError:
            raise ValueError('Invalid fetch time: {}'.format(tokens[0]))

        try:
            config = json.loads(tokens[2])
        except ValueError as e:
            raise ValueError('Invalid config JSON: {}. {}'.format(tokens[2], str(e)))

        return ConfigEntry(config=config, etag=tokens[1], fetch_time=fetch_time)


ConfigEntry.empty = ConfigEntry(etag='empty')
