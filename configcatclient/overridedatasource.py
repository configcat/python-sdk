from abc import ABCMeta, abstractmethod
from enum import IntEnum


class OverrideBehaviour(IntEnum):
    # When evaluating values, the SDK will not use feature flags & settings from the ConfigCat CDN, but it will use
    # all feature flags & settings that are loaded from local-override sources.
    LocalOnly = 0,

    # When evaluating values, the SDK will use all feature flags & settings that are downloaded from the ConfigCat CDN,
    # plus all feature flags & settings that are loaded from local-override sources. If a feature flag or a setting is
    # defined both in the fetched and the local-override source then the local-override version will take precedence.
    LocalOverRemote = 1,

    # When evaluating values, the SDK will use all feature flags & settings that are downloaded from the ConfigCat CDN,
    # plus all feature flags & settings that are loaded from local-override sources. If a feature flag or a setting is
    # defined both in the fetched and the local-override source then the fetched version will take precedence.
    RemoteOverLocal = 2


class OverrideDataSource(object):
    __metaclass__ = ABCMeta

    def __init__(self, override_behaviour):
        self._override_behaviour = override_behaviour

    def get_behaviour(self):
        return self._override_behaviour

    @abstractmethod
    def get_overrides(self):
        """
        :returns the override dictionary
        """
