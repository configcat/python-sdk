import sys

from .config import extend_config_with_inline_salt_and_segment, VALUE, FEATURE_FLAGS, BOOL_VALUE, STRING_VALUE, \
    INT_VALUE, DOUBLE_VALUE, SettingType, SETTING_TYPE, UNSUPPORTED_VALUE
from .overridedatasource import OverrideDataSource, FlagOverrides
import json
import os

from .utils import unicode_to_utf8


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
        self._config = None
        self._cached_file_stamp = 0

    def get_overrides(self):
        self._reload_file_content()
        return self._config

    def _reload_file_content(self):  # noqa: C901
        try:
            stamp = os.stat(self._file_path).st_mtime
            if stamp != self._cached_file_stamp:
                self._cached_file_stamp = stamp
                with open(self._file_path) as file:
                    data = json.load(file)

                    if sys.version_info[0] == 2:
                        data = unicode_to_utf8(data)  # On Python 2.7, convert unicode to utf-8

                    if 'flags' in data:
                        self._config = {FEATURE_FLAGS: {}}
                        source = data['flags']
                        for key, value in source.items():
                            if isinstance(value, bool):
                                value_type = BOOL_VALUE
                            elif isinstance(value, str):
                                value_type = STRING_VALUE
                            elif isinstance(value, int):
                                value_type = INT_VALUE
                            elif isinstance(value, float):
                                value_type = DOUBLE_VALUE
                            else:
                                value_type = UNSUPPORTED_VALUE

                            self._config[FEATURE_FLAGS][key] = {VALUE: {value_type: value}}
                            setting_type = SettingType.from_type(type(value))
                            if setting_type is not None:
                                self._config[FEATURE_FLAGS][key][SETTING_TYPE] = int(setting_type)
                    else:
                        extend_config_with_inline_salt_and_segment(data)
                        self._config = data
        except OSError:
            self.log.exception('Failed to read the local config file \'%s\'.', self._file_path, event_id=1302)
        except ValueError:
            self.log.exception('Failed to decode JSON from the local config file \'%s\'.', self._file_path, event_id=2302)
