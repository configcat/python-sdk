import sys

from .config import VALUE, FEATURE_FLAGS, BOOL_VALUE, STRING_VALUE, INT_VALUE, DOUBLE_VALUE, SettingType, SETTING_TYPE, \
    UNSUPPORTED_VALUE
from .overridedatasource import OverrideDataSource, FlagOverrides
from .utils import unicode_to_utf8


class LocalDictionaryFlagOverrides(FlagOverrides):
    def __init__(self, source, override_behaviour):
        self.source = source
        self.override_behaviour = override_behaviour

        if sys.version_info[0] == 2:
            self.source = unicode_to_utf8(self.source)  # On Python 2.7, convert unicode to utf-8

    def create_data_source(self, log):
        return LocalDictionaryDataSource(self.source, self.override_behaviour, log)


class LocalDictionaryDataSource(OverrideDataSource):
    def __init__(self, source, override_behaviour, log):
        OverrideDataSource.__init__(self, override_behaviour=override_behaviour)
        self.log = log
        self._config = {}
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

            if FEATURE_FLAGS not in self._config:
                self._config[FEATURE_FLAGS] = {}

            self._config[FEATURE_FLAGS][key] = {VALUE: {value_type: value}}
            setting_type = SettingType.from_type(type(value))
            if setting_type is not None:
                self._config[FEATURE_FLAGS][key][SETTING_TYPE] = int(setting_type)

    def get_overrides(self):
        return self._config
