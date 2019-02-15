import requests
import logging
import sys
from cachecontrol import CacheControl
from .interfaces import ConfigFetcher
from .version import CONFIGCATCLIENT_VERSION

if sys.version_info < (2, 7, 9):
    requests.packages.urllib3.disable_warnings()

BASE_URL = 'https://cdn.configcat.com'
BASE_PATH = 'configuration-files/'
BASE_EXTENSION = '/config_v2.json'

log = logging.getLogger(sys.modules[__name__].__name__)


class CacheControlConfigFetcher(ConfigFetcher):

    def __init__(self, api_key, mode, base_url=None):
        self._api_key = api_key
        self._session = requests.Session()
        self._request_cache = CacheControl(self._session)
        self._headers = {'User-Agent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'X-ConfigCat-UserAgent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'Content-Type': "application/json"}
        if base_url is not None:
            self._base_url = base_url.rstrip('/')
        else:
            self._base_url = BASE_URL

    def get_configuration_json(self):
        log.debug("Fetching configuration from ConfigCat")
        uri = self._base_url + '/' + BASE_PATH + self._api_key + BASE_EXTENSION
        response = self._request_cache.get(uri, headers=self._headers, timeout=(10, 30))
        response.raise_for_status()
        json = response.json()
        log.debug("ConfigCat configuration json fetch response code:[%d] Cached:[%s]",
                  response.status_code, response.from_cache)

        return json

    def close(self):
        if self._session:
            self._session.close()
