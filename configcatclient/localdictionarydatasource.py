from .constants import VALUE
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
        self._settings = {}
        for key, value in source.items():
            self._settings[key] = {VALUE: value}

    def get_overrides(self):
        return self._settings
