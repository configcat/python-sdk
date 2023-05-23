from .constants import VALUE, FEATURE_FLAGS, BOOL_VALUE, STRING_VALUE, INT_VALUE, DOUBLE_VALUE, SETTING_TYPE
from .overridedatasource import OverrideDataSource, FlagOverrides


class LocalDictionaryFlagOverrides(FlagOverrides):
    def __init__(self, source, override_behaviour):
        self.source = source
        self.override_behaviour = override_behaviour

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
            else:
                value_type = DOUBLE_VALUE

            if FEATURE_FLAGS not in self._config:
                self._config[FEATURE_FLAGS] = {}
            self._config[FEATURE_FLAGS][key] = {VALUE: {value_type: value}}

    def get_overrides(self):
        return self._config
