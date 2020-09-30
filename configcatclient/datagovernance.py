from enum import IntEnum


class DataGovernance(IntEnum):
    """
    Restrict the location of your feature flag and setting data within the ConfigCat CDN. \n
    Global: Your data will be published to all ConfigCat CDN nodes to guarantee lowest response times. \n
    EuOnly: Your data will be published to CDN nodes only in the EU.
    """
    Global = 0
    EuOnly = 1
