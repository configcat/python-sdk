import requests
import sys
from enum import IntEnum
from platform import python_version

from .datagovernance import DataGovernance
from .utils import get_utc_now_seconds_since_epoch
from .version import CONFIGCATCLIENT_VERSION
from .constants import *

if sys.version_info < (2, 7, 9):
    requests.packages.urllib3.disable_warnings()

BASE_URL_GLOBAL = 'https://cdn-global.configcat.com'
BASE_URL_EU_ONLY = 'https://cdn-eu.configcat.com'
BASE_PATH = 'configuration-files/'
BASE_EXTENSION = '/' + CONFIG_FILE_NAME + '.json'


class RedirectMode(IntEnum):
    NoRedirect = 0,
    ShouldRedirect = 1,
    ForceRedirect = 2


class FetchResponse(object):
    ETAG = 'etag'
    FETCH_TIME = 'fetch_time'
    CONFIG = 'config'

    def __init__(self, response, etag='', fetch_time=None):
        self._response = response
        self._etag = etag
        self._fetch_time = fetch_time if fetch_time is not None else get_utc_now_seconds_since_epoch()

    def json(self):
        """Returns the json-encoded content of a response, if any.
        :raises ValueError: If the response body does not contain valid json.
        """
        json = self._response.json()
        return {FetchResponse.ETAG: self._etag,
                FetchResponse.FETCH_TIME: self._fetch_time,
                FetchResponse.CONFIG: json}

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
    def __init__(self, sdk_key, log, mode, base_url=None, proxies=None, proxy_auth=None,
                 connect_timeout=10, read_timeout=30, data_governance=DataGovernance.Global):
        self._sdk_key = sdk_key
        self.log = log
        self._proxies = proxies
        self._proxy_auth = proxy_auth
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._headers = {'User-Agent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'X-ConfigCat-UserAgent': 'ConfigCat-Python/' + mode + '-' + CONFIGCATCLIENT_VERSION,
                         'X-ConfigCat-PythonVersion': python_version(),
                         'Content-Type': "application/json"}
        if base_url is not None:
            self._base_url_overridden = True
            self._base_url = base_url.rstrip('/')
        else:
            self._base_url_overridden = False
            if data_governance == DataGovernance.EuOnly:
                self._base_url = BASE_URL_EU_ONLY
            else:
                self._base_url = BASE_URL_GLOBAL

    def get_connect_timeout(self):
        return self._connect_timeout

    def get_read_timeout(self):
        return self._read_timeout

    def get_configuration_json(self, etag='', retries=0):
        """
        :return: Returns the FetchResponse object contains configuration json Dictionary
        """
        uri = self._base_url + '/' + BASE_PATH + self._sdk_key + BASE_EXTENSION
        headers = self._headers
        if etag:
            headers['If-None-Match'] = etag
        else:
            headers['If-None-Match'] = None

        response = requests.get(uri, headers=headers, timeout=(self._connect_timeout, self._read_timeout),
                                proxies=self._proxies, auth=self._proxy_auth)
        response.raise_for_status()
        response_etag = response.headers.get('Etag')
        if response_etag is None:
            response_etag = ''

        fetch_response = FetchResponse(response, response_etag)

        # If there wasn't a config change, we return the response.
        if not fetch_response.is_fetched():
            return fetch_response

        preferences = fetch_response.json()[FetchResponse.CONFIG].get(PREFERENCES, None)
        if preferences is None:
            return fetch_response

        base_url = preferences.get(BASE_URL)

        # If the base_url is the same as the last called one, just return the response.
        if base_url is None or self._base_url == base_url:
            return fetch_response

        redirect = preferences.get(REDIRECT)
        # If the base_url is overridden, and the redirect parameter is not 2 (force),
        # the SDK should not redirect the calls and it just have to return the response.
        if self._base_url_overridden and redirect != int(RedirectMode.ForceRedirect):
            return fetch_response

        # The next call should use the base_url provided in the config json
        self._base_url = base_url

        # If the redirect property == 0 (redirect not needed), return the response
        if redirect == int(RedirectMode.NoRedirect):
            # Return the response
            return fetch_response

        # Try to download again with the new url

        if redirect == int(RedirectMode.ShouldRedirect):
            self.log.warning('Your data_governance parameter at ConfigCatClient initialization is not in sync '
                             'with your preferences on the ConfigCat Dashboard: '
                             'https://app.configcat.com/organization/data-governance. '
                             'Only Organization Admins can access this preference.')

        # To prevent loops we check if we retried at least 3 times with the new base_url
        if retries >= 2:
            self.log.error('Redirect loop during config.json fetch. Please contact support@configcat.com.')
            return fetch_response

        # Retry the config download with the new base_url
        return self.get_configuration_json(etag, retries + 1)
