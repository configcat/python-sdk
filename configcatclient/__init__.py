from .configcatclient import ConfigCatClient
from .interfaces import ConfigCatClientException  # noqa: F401
from .datagovernance import DataGovernance  # noqa: F401
from .configcatoptions import ConfigCatOptions  # noqa: F401
from .pollingmode import PollingMode  # noqa: F401


def get(sdk_key, options=None):
    """
    Creates a new or gets an already existing `ConfigCatClient` for the given `sdk_key`.

    :param sdk_key: ConfigCat SDK Key to access your configuration.
    :param options: Configuration `ConfigCatOptions` for `ConfigCatClient`.
    :return: the `ConfigCatClient` instance.
    """
    return ConfigCatClient.get(sdk_key=sdk_key, options=options)


def close_all():
    """
    Closes all ConfigCatClient instances.
    """
    ConfigCatClient.close_all()
