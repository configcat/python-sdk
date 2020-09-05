import requests
import logging
import sys

from .datalocation import DataLocation
from .version import CONFIGCATCLIENT_VERSION
from .constants import *

if sys.version_info < (2, 7, 9):
    requests.packages.urllib3.disable_warnings()

BASE_URL_GLOBAL = 'https://cdn-global.configcat.com'
BASE_URL_EUONLY = 'https://cdn-eu.configcat.com'
BASE_PATH = 'configuration-files/'
BASE_EXTENSION = '/config_v5.json'

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
    def __init__(self, sdk_key, mode, base_url=None, proxies=None, proxy_auth=None, data_location=DataLocation.Global):
        self._sdk_key = sdk_key
        self._proxies = proxies
        self._proxy_auth = proxy_auth
        self._etag = ''
        self._headers = {'User-Agent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'X-ConfigCat-UserAgent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'Content-Type': "application/json"}
        if base_url is not None:
            self._base_url_overridden = True
            self._base_url = base_url.rstrip('/')
        else:
            self._base_url_overridden = False
            if data_location == DataLocation.EuOnly:
                self._base_url = BASE_URL_EUONLY
            else:
                self._base_url = BASE_URL_GLOBAL

    def get_configuration_json(self, force_fetch=False, retries=0):
        """
        :return: Returns the FetchResponse object contains configuration json Dictionary
        """
        uri = self._base_url + '/' + BASE_PATH + self._sdk_key + BASE_EXTENSION
        headers = self._headers
        if self._etag and not force_fetch:
            headers['If-None-Match'] = self._etag
        else:
            headers['If-None-Match'] = None

        response = requests.get(uri, headers=headers, timeout=(10, 30),
                                proxies=self._proxies, auth=self._proxy_auth)
        response.raise_for_status()
        etag = response.headers.get('Etag')
        if etag:
            self._etag = etag

        fetch_response = FetchResponse(response)

        # If the base_url is overridden, the SDK should not redirect the calls and it just have to return the response.
        if self._base_url_overridden:
            return fetch_response

        # If there wasn't a config change, we return the response.
        if not fetch_response.is_fetched():
            return fetch_response

        preferences = fetch_response.json().get(PREFERENCES, None)
        if preferences is None:
            return fetch_response

        base_url = preferences.get(BASE_URL)

        # If the base_url is the same as the last called one, just return the response.
        if base_url is None or self._base_url == base_url:
            return fetch_response

        # The next call should use the base_url provided in the config json
        self._base_url = base_url

        # If the redirect property is false, return the response
        redirect = preferences.get(REDIRECT)
        if redirect is None or not redirect:
            return fetch_response

        # To prevent loops we check if we retried at least 3 times with the new base_url
        if retries > 3:
            return fetch_response

        # Retry the config download with the new base_url
        return self.get_configuration_json(force_fetch, retries+1)
