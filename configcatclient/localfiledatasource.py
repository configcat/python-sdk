from .overridedatasource import OverrideDataSource
from .constants import *
import json
import os


class LocalFileDataSource(OverrideDataSource):
    def __init__(self, file_path, override_behaviour):
        OverrideDataSource.__init__(self, override_behaviour=override_behaviour)
        self._file_path = file_path
        self._cached_file_stamp = 0

    def get_overrides(self):
        stamp = os.stat(self._file_path).st_mtime
        if stamp != self._cached_file_stamp:
            self._cached_file_stamp = stamp
            self._reload_file_content()

        return self._settings

    def _reload_file_content(self):
        file = open(self._file_path)
        data = json.load(file)
        file.close()
        if 'flags' in data:
            dictionary = {}
            source = data['flags']
            for key, value in source.items():
                dictionary[key] = {VALUE: value}
            self._settings = {FEATURE_FLAGS: dictionary}
        else:
            self._settings = data
