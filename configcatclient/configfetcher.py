import requests
import logging
import sys
from .version import CONFIGCATCLIENT_VERSION

if sys.version_info < (2, 7, 9):
    requests.packages.urllib3.disable_warnings()

BASE_URL = 'https://cdn.configcat.com'
BASE_PATH = 'configuration-files/'
BASE_EXTENSION = '/config_v4.json'

log = logging.getLogger(sys.modules[__name__].__name__)


class FetchResponse(object):

    def __init__(self, response):
        self._response = response

    def json(self):
        """Returns the json-encoded content of a response, if any.
        :raises ValueError: If the response body does not contain valid json.
        """
        return self._response.json()

    def is_fetched(self):
        """Gets whether a new configuration value was fetched or not.
        :return: True if a new configuration value was fetched, otherwise false.
        """
        return 200 <= self._response.status_code < 300

    def is_not_modified(self):
        """Gets whether the fetch resulted a '304 Not Modified' or not.
        :return: True if the fetch resulted a '304 Not Modified' code, otherwise false.
        """
        return self._response.status_code == 304


class ConfigFetcher(object):

    def __init__(self, sdk_key, mode, base_url=None, proxies=None, proxy_auth=None):
        self._sdk_key = sdk_key
        self._proxies = proxies
        self._proxy_auth = proxy_auth
        self._etag = ''
        self._headers = {'User-Agent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'X-ConfigCat-UserAgent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'Content-Type': "application/json"}
        if base_url is not None:
            self._base_url = base_url.rstrip('/')
        else:
            self._base_url = BASE_URL

    def get_configuration_json(self):
        """
        :return: Returns the FetchResponse object contains configuration json Dictionary
        """
        uri = self._base_url + '/' + BASE_PATH + self._sdk_key + BASE_EXTENSION
        headers = self._headers
        if self._etag:
            headers['If-None-Match'] = self._etag

        response = requests.get(uri, headers=headers, timeout=(10, 30),
                                proxies=self._proxies, auth=self._proxy_auth)
        response.raise_for_status()
        etag = response.headers.get('Etag')
        if etag:
            self._etag = etag

        return FetchResponse(response)
