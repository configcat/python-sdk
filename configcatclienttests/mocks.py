import json
import time

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

    def get_configuration_json(self, etag=''):
        self._call_count += 1
        if etag != self._etag:
            self._fetch_count += 1
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = self._configuration
        return FetchResponse(response_mock, self._etag)

    def set_configuration_json(self, value):
        self._configuration = value

    @property
    def get_call_count(self):
        return self._call_count

    @property
    def get_fetch_count(self):
        return self._fetch_count


class ConfigFetcherWithErrorMock(ConfigFetcher):
    def __init__(self, exception):
        self._exception = exception

    def get_configuration_json(self, etag=''):
        raise self._exception


class ConfigFetcherWaitMock(ConfigFetcher):
    def __init__(self, wait_seconds):
        self._wait_seconds = wait_seconds

    def get_configuration_json(self, etag=''):
        time.sleep(self._wait_seconds)
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = TEST_JSON
        return FetchResponse(response_mock)


class ConfigFetcherCountMock(ConfigFetcher):
    def __init__(self):
        self._value = 0

    def get_configuration_json(self, etag=''):
        self._value += 10
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = self._value
        return FetchResponse(response_mock)


class ConfigCacheMock(ConfigCache):
    def get(self, key):
        return {FetchResponse.CONFIG: TEST_OBJECT}

    def set(self, key, value):
        pass


class CallCounter(object):
    def __init__(self):
        self._call_count = 0

    def callback(self):
        self._call_count += 1

    def callback_exception(self):
        self._call_count += 1
        raise Exception("error")

    @property
    def get_call_count(self):
        return self._call_count


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
