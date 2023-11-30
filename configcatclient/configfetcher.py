import requests
import sys
from enum import IntEnum
from platform import python_version
from requests import HTTPError
from requests import Timeout

from .config import extend_config_with_inline_salt_and_segment
from .configentry import ConfigEntry
from .config import CONFIG_FILE_NAME, PREFERENCES, BASE_URL, REDIRECT
from .datagovernance import DataGovernance
from .logger import Logger
from .utils import get_utc_now_seconds_since_epoch, unicode_to_utf8
from .version import CONFIGCATCLIENT_VERSION

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


class Status(IntEnum):
    Fetched = 0,
    NotModified = 1,
    Failure = 2


class FetchResponse(object):
    def __init__(self, status, entry, error=None, is_transient_error=False):
        self._status = status
        self.entry = entry
        self.error = error
        self.is_transient_error = is_transient_error

    def is_fetched(self):
        """Gets whether a new configuration value was fetched or not.
        :return: True if a new configuration value was fetched, otherwise False.
        """
        return self._status == Status.Fetched

    def is_not_modified(self):
        """Gets whether the fetch resulted a '304 Not Modified' or not.
        :return: True if the fetch resulted a '304 Not Modified' code, otherwise False.
        """
        return self._status == Status.NotModified

    def is_failed(self):
        """Gets whether the fetch failed or not.
        :return: True if the fetch failed, otherwise False.
        """
        return self._status == Status.Failure

    @classmethod
    def success(cls, entry):
        return FetchResponse(Status.Fetched, entry)

    @classmethod
    def not_modified(cls):
        return FetchResponse(Status.NotModified, ConfigEntry.empty)

    @classmethod
    def failure(cls, error, is_transient_error):
        return FetchResponse(Status.Failure, ConfigEntry.empty, error, is_transient_error)


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

    def get_configuration(self, etag='', retries=0):
        """
        :return: Returns the FetchResponse object contains configuration entry
        """
        fetch_response = self._fetch(etag)

        # If there wasn't a config change, we return the response.
        if not fetch_response.is_fetched():
            return fetch_response

        preferences = fetch_response.entry.config.get(PREFERENCES, None)
        if preferences is None:
            return fetch_response

        base_url = preferences.get(BASE_URL)

        # If the base_url is the same as the last called one, just return the response.
        if base_url is None or self._base_url == base_url:
            return fetch_response

        redirect = preferences.get(REDIRECT)
        # If the base_url is overridden, and the redirect parameter is not 2 (force),
        # the SDK should not redirect the calls, and it just has to return the response.
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
            self.log.warning('The `dataGovernance` parameter specified at the client initialization is not in sync '
                             'with the preferences on the ConfigCat Dashboard. '
                             'Read more: https://configcat.com/docs/advanced/data-governance/',
                             event_id=3002)

        # To prevent loops we check if we retried at least 3 times with the new base_url
        if retries >= 2:
            self.log.error('Redirection loop encountered while trying to fetch config JSON. '
                           'Please contact us at https://configcat.com/support/', event_id=1104)
            return fetch_response

        # Retry the config download with the new base_url
        return self.get_configuration(etag, retries + 1)

    def _fetch(self, etag):  # noqa: C901
        uri = self._base_url + '/' + BASE_PATH + self._sdk_key + BASE_EXTENSION
        headers = self._headers
        if etag:
            headers['If-None-Match'] = etag
        else:
            headers['If-None-Match'] = None

        try:
            response = requests.get(uri, headers=headers, timeout=(self._connect_timeout, self._read_timeout),
                                    proxies=self._proxies, auth=self._proxy_auth)
            response.raise_for_status()

            if response.status_code in [200, 201, 202, 203, 204]:
                response_etag = response.headers.get('ETag')
                if response_etag is None:
                    response_etag = ''
                config = response.json()
                extend_config_with_inline_salt_and_segment(config)
                if sys.version_info[0] == 2:
                    config = unicode_to_utf8(config)  # On Python 2.7, convert unicode to utf-8
                    config_json_string = response.text.encode('utf-8')
                else:
                    config_json_string = response.text

                return FetchResponse.success(
                    ConfigEntry(config, response_etag, config_json_string, get_utc_now_seconds_since_epoch()))
            elif response.status_code == 304:
                return FetchResponse.not_modified()
            elif response.status_code in [404, 403]:
                error = 'Your SDK Key seems to be wrong. ' \
                        'You can find the valid SDK Key at https://app.configcat.com/sdkkey. ' \
                        'Received unexpected response: %s'
                error_args = (str(response), )
                self.log.error(error, *error_args, event_id=1100)
                return FetchResponse.failure(Logger.format(error, error_args), False)
            else:
                raise (requests.HTTPError(response))
        except HTTPError as e:
            error = 'Unexpected HTTP response was received while trying to fetch config JSON: %s'
            error_args = (str(e.response), )
            self.log.error(error, *error_args, event_id=1101)
            return FetchResponse.failure(Logger.format(error, error_args), True)
        except Timeout:
            error = 'Request timed out while trying to fetch config JSON. Timeout values: [connect: %gs, read: %gs]'
            error_args = (self.get_connect_timeout(), self.get_read_timeout())
            self.log.error(error, *error_args, event_id=1102)
            return FetchResponse.failure(Logger.format(error, error_args), True)
        except Exception as e:
            error = 'Unexpected error occurred while trying to fetch config JSON.'
            self.log.exception(error, event_id=1103)
            return FetchResponse.failure(Logger.format(error, (), e), True)
