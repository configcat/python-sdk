import requests
import logging
import sys
from cachecontrol import CacheControl

from .interfaces import ConfigFetcher
from .version import CONFIGCATCLIENT_VERSION

if sys.version_info < (2, 7, 9):
    requests.packages.urllib3.disable_warnings()

BASE_URI = 'https://cdn.configcat.com/configuration-files/'
BASE_EXTENSION = '/config_v2.json'

log = logging.getLogger(sys.modules[__name__].__name__)


class CacheControlConfigFetcher(ConfigFetcher):

    def __init__(self, api_key, mode):
        self._api_key = api_key
        self._session = requests.Session()
        self._request_cache = CacheControl(self._session)
        self._headers = {'User-Agent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'X-ConfigCat-UserAgent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'Content-Type': "application/json"}

    def get_configuration_json(self):
        log.debug("Fetching configuration from ConfigCat")

        uri = BASE_URI + self._api_key + BASE_EXTENSION
        response = self._request_cache.get(uri, headers=self._headers, timeout=(10, 30))
        response.raise_for_status()
        json = response.json()
        log.debug("ConfigCat configuration json fetch response code:[%d] Cached:[%s]",
                  response.status_code, response.from_cache)

        return json

    def close(self):
        if self._session:
            self._session.close()
