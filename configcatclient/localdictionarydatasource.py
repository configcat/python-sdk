from .constants import VALUE, FEATURE_FLAGS
from .overridedatasource import OverrideDataSource


class LocalDictionaryDataSource(OverrideDataSource):
    def __init__(self, source, override_behaviour):
        OverrideDataSource.__init__(self, override_behaviour=override_behaviour)
        dictionary = {}
        for key, value in source.items():
            dictionary[key] = {VALUE: value}
        self._settings = {FEATURE_FLAGS: dictionary}

    def get_overrides(self):
        return self._settings
