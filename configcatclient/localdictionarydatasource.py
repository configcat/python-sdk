from .constants import VALUE, FEATURE_FLAGS
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
        dictionary = {}
        for key, value in source.items():
            dictionary[key] = {VALUE: value}
        self._settings = {FEATURE_FLAGS: dictionary}

    def get_overrides(self):
        return self._settings
