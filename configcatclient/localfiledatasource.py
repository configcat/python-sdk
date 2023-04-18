from .constants import VALUE, FEATURE_FLAGS
from .overridedatasource import OverrideDataSource, FlagOverrides
import json
import os


class LocalFileFlagOverrides(FlagOverrides):
    def __init__(self, file_path, override_behaviour):
        self.file_path = file_path
        self.override_behaviour = override_behaviour

    def create_data_source(self, log):
        return LocalFileDataSource(self.file_path, self.override_behaviour, log)


class LocalFileDataSource(OverrideDataSource):
    def __init__(self, file_path, override_behaviour, log):
        OverrideDataSource.__init__(self, override_behaviour=override_behaviour)
        self.log = log
        if not os.path.exists(file_path):
            self.log.error('Cannot find the local config file \'%s\'. '
                           'This is a path that your application provided to the ConfigCat SDK '
                           'by passing it to the constructor of the `LocalFileFlagOverrides` class. '
                           'Read more: https://configcat.com/docs/sdk-reference/python/#json-file',
                           file_path, event_id=1300)

        self._file_path = file_path
        self._settings = None
        self._cached_file_stamp = 0

    def get_overrides(self):
        self._reload_file_content()
        return self._settings

    def _reload_file_content(self):
        try:
            stamp = os.stat(self._file_path).st_mtime
            if stamp != self._cached_file_stamp:
                self._cached_file_stamp = stamp
                with open(self._file_path) as file:
                    data = json.load(file)
                    if 'flags' in data:
                        self._settings = {}
                        source = data['flags']
                        for key, value in source.items():
                            self._settings[key] = {VALUE: value}
                    else:
                        self._settings = data[FEATURE_FLAGS]
        except OSError:
            self.log.exception('Failed to read the local config file \'%s\'.', self._file_path, event_id=1302)
        except ValueError:
            self.log.exception('Failed to decode JSON from the local config file \'%s\'.', self._file_path, event_id=2302)
