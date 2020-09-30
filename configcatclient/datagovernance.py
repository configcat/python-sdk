from enum import IntEnum


class DataGovernance(IntEnum):
    """
    Control the location of the config.json files containing your feature flags
    and settings within the ConfigCat CDN. \n
    Global: Your data will be published to all ConfigCat CDN nodes to guarantee lowest response times. \n
    EuOnly: Your data will be published to CDN nodes only in the EU.
    """
    Global = 0
    EuOnly = 1
