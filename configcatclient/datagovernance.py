from enum import IntEnum


class DataGovernance(IntEnum):
    """
    Control the location of the config.json files containing your feature flags
    and settings within the ConfigCat CDN. \n
    Global: If your data is published to all global ConfigCat CDN nodes. \n
    EuOnly: If your data is published to CDN nodes only in the EU.
    """
    Global = 0
    EuOnly = 1
