from .constants import VALUE, FEATURE_FLAGS
from .overridedatasource import OverrideDataSource
import json
import os
import logging
import sys

log = logging.getLogger(sys.modules[__name__].__name__)


class LocalFileDataSource(OverrideDataSource):
    def __init__(self, file_path, override_behaviour):
        OverrideDataSource.__init__(self, override_behaviour=override_behaviour)
        if not os.path.exists(file_path):
            log.error('The file \'%s\' does not exists.' % file_path)

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
                        dictionary = {}
                        source = data['flags']
                        for key, value in source.items():
                            dictionary[key] = {VALUE: value}
                        self._settings = {FEATURE_FLAGS: dictionary}
                    else:
                        self._settings = data
        except OSError as e:
            log.error('Could not read the content of the file %s. %s' % (self._file_path, e))
        except json.decoder.JSONDecodeError as e:
            log.error('Could not decode json from file %s. %s' % (self._file_path, e))

