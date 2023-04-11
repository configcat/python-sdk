from __future__ import annotations

from . import utils


class ConfigEntry:
    CONFIG = 'config'
    ETAG = 'etag'
    FETCH_TIME = 'fetch_time'
    empty: ConfigEntry

    def __init__(self, config={}, etag='', fetch_time=utils.distant_past):
        self.config = config
        self.etag = etag
        self.fetch_time = fetch_time

    @classmethod
    def create_from_json(cls, json):
        if not json:
            return ConfigEntry.empty

        return ConfigEntry(
            config=json.get(ConfigEntry.CONFIG, {}),
            etag=json.get(ConfigEntry.ETAG, ''),
            fetch_time=json.get(ConfigEntry.FETCH_TIME, utils.distant_past)
        )

    def is_empty(self):
        return self == ConfigEntry.empty

    def to_json(self):
        return {
            ConfigEntry.CONFIG: self.config,
            ConfigEntry.ETAG: self.etag,
            ConfigEntry.FETCH_TIME: self.fetch_time
        }


ConfigEntry.empty = ConfigEntry(etag='empty')
