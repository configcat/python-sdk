import json
import time

from configcatclient.configentry import ConfigEntry
from configcatclient.constants import FEATURE_FLAGS
from configcatclient.utils import get_utc_now_seconds_since_epoch

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


from configcatclient.configfetcher import FetchResponse, ConfigFetcher
from configcatclient.interfaces import ConfigCache

TEST_JSON = '{' \
            '   "p": {' \
            '       "u": "https://cdn-global.configcat.com",' \
            '       "r": 0' \
            '   },' \
            '   "f": {' \
            '       "testKey": { "v": "testValue", "t": 1, "p": [], "r": [] }' \
            '   }' \
            '}'

TEST_JSON_FORMAT = '{{ "f": {{ "testKey": {{ "v": {value}, "p": [], "r": [] }} }} }}'

TEST_JSON2 = '{' \
             '  "p": {' \
             '       "u": "https://cdn-global.configcat.com",' \
             '       "r": 0' \
             '  },' \
             '  "f": {' \
             '      "testKey": { "v": "testValue", "t": 1, "p": [], "r": [] }, ' \
             '      "testKey2": { "v": "testValue2", "t": 1, "p": [], "r": [] }' \
             '  }' \
             '}'

TEST_OBJECT = json.loads(
    '{'
    '"p": {'
    '"u": "https://cdn-global.configcat.com",'
    '"r": 0'
    "},"
    '"f": {'
    '"testBoolKey": '
    '{"v": true, "t": 0, "p": [], "r": []},'
    '"testStringKey": '
    '{"v": "testValue", "i": "id", "t": 1, "p": [], "r": ['
    '   {"i":"id1","v":"fake1","a":"Identifier","t":2,"c":"@test1.com"},'
    '   {"i":"id2","v":"fake2","a":"Identifier","t":2,"c":"@test2.com"}'
    ']},'
    '"testIntKey": '
    '{"v": 1, "t": 2, "p": [], "r": []},'
    '"testDoubleKey": '
    '{"v": 1.1, "t": 3,"p": [], "r": []},'
    '"key1": '
    '{"v": true, "i": "fakeId1","p": [], "r": []},'
    '"key2": '
    '{"v": false, "i": "fakeId2","p": [], "r": []}'
    '}'
    '}')


class ConfigFetcherMock(ConfigFetcher):
    def __init__(self):
        self._call_count = 0
        self._fetch_count = 0
        self._configuration = TEST_JSON
        self._etag = 'test_etag'

    def get_configuration(self, etag=''):
        self._call_count += 1
        if etag != self._etag:
            self._fetch_count += 1
            return FetchResponse.success(
                ConfigEntry(json.loads(self._configuration), self._etag, get_utc_now_seconds_since_epoch())
            )
        return FetchResponse.not_modified()

    def set_configuration_json(self, value):
        if self._configuration != value:
            self._configuration = value
            self._etag += '_etag'

    @property
    def get_call_count(self):
        return self._call_count

    @property
    def get_fetch_count(self):
        return self._fetch_count


class ConfigFetcherWithErrorMock(ConfigFetcher):
    def __init__(self, error):
        self._error = error

    def get_configuration(self, etag=''):
        return FetchResponse.failure(self._error)


class ConfigFetcherWaitMock(ConfigFetcher):
    def __init__(self, wait_seconds):
        self._wait_seconds = wait_seconds

    def get_configuration(self, etag=''):
        time.sleep(self._wait_seconds)
        return FetchResponse.success(ConfigEntry(json.loads(TEST_JSON)))


class ConfigFetcherCountMock(ConfigFetcher):
    def __init__(self):
        self._value = 0

    def get_configuration(self, etag=''):
        self._value += 1
        config = json.loads(TEST_JSON_FORMAT.format(value=self._value))
        return FetchResponse.success(ConfigEntry(config))


class ConfigCacheMock(ConfigCache):
    def get(self, key):
        return json.dumps({ConfigEntry.CONFIG: TEST_OBJECT, ConfigEntry.ETAG: 'test-etag'})

    def set(self, key, value):
        pass


class SingleValueConfigCache(ConfigCache):

    def __init__(self, value):
        self._value = value

    def get(self, key):
        return self._value

    def set(self, key, value):
        self._value = value


class MockHeader:
    def __init__(self, etag):
        self.etag = etag

    def get(self, name):
        if name == 'Etag':
            return self.etag
        return None


class MockResponse:
    def __init__(self, json_data, status_code, etag=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = MockHeader(etag)

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if 200 <= self.status_code < 300 or self.status_code == 304:
            return
        raise Exception(self.status_code)


class HookCallbacks(object):
    def __init__(self):
        self.is_ready = False
        self.is_ready_call_count = 0
        self.changed_config = None
        self.changed_config_call_count = 0
        self.evaluation_details = None
        self.evaluation_details_call_count = 0
        self.error = None
        self.error_call_count = 0
        self.callback_exception_call_count = 0

    def on_client_ready(self):
        self.is_ready = True
        self.is_ready_call_count += 1

    def on_config_changed(self, config):
        self.changed_config = config
        self.changed_config_call_count += 1

    def on_flag_evaluated(self, evaluation_details):
        self.evaluation_details = evaluation_details
        self.evaluation_details_call_count += 1

    def on_error(self, error):
        self.error = error
        self.error_call_count += 1

    def callback_exception(self, *args, **kwargs):
        self.callback_exception_call_count += 1
        raise Exception("error")

