from enum import IntEnum


class DataGovernance(IntEnum):
    """
    Control the location of the config.json files containing your feature flags
    and settings within the ConfigCat CDN. \n
    Global: Select this if your feature flags are published to all global CDN nodes. \n
    EuOnly: Select this if your feature flags are published to CDN nodes only in the EU.
    """
    Global = 0
    EuOnly = 1
