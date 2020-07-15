import json
import time

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


from configcatclient.configfetcher import FetchResponse, ConfigFetcher
from configcatclient.interfaces import ConfigCache

TEST_JSON = '{"testKey": { "v": "testValue", "t": 1, ' \
            '"p": [], "r": [] }}'

TEST_JSON2 = '{"testKey": { "v": "testValue", "t": 1, ' \
             '"p": [], "r": [] }, ' \
             '"testKey2": { "v": "testValue2", "t": 1, ' \
             '"p": [], "r": [] }}'

TEST_OBJECT = json.loads(
    '{"testBoolKey": '
    '{"v": true,"t": 0, "p": [],"r": []},'
    '"testStringKey": '
    '{"v": "testValue","t": 1, "p": [],"r": []},'
    '"testIntKey": '
    '{"v": 1,"t": 2, "p": [],"r": []},'
    '"testDoubleKey": '
    '{"v": 1.1,"t": 3,"p": [],"r": []}}')


class ConfigFetcherMock(ConfigFetcher):
    def __init__(self):
        self._call_count = 0
        self._configuration = TEST_JSON

    def get_configuration_json(self, force_fetch=False):
        self._call_count = self._call_count + 1
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = self._configuration
        return FetchResponse(response_mock)

    def set_configuration_json(self, value):
        self._configuration = value

    @property
    def get_call_count(self):
        return self._call_count


class ConfigFetcherWithErrorMock(ConfigFetcher):
    def __init__(self, exception):
        self._exception = exception

    def get_configuration_json(self, force_fetch=False):
        raise self._exception


class ConfigFetcherWaitMock(ConfigFetcher):
    def __init__(self, wait_seconds):
        self._wait_seconds = wait_seconds

    def get_configuration_json(self, force_fetch=False):
        time.sleep(self._wait_seconds)
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = TEST_JSON
        return FetchResponse(response_mock)


class ConfigFetcherCountMock(ConfigFetcher):
    def __init__(self):
        self._value = 0

    def get_configuration_json(self, force_fetch=False):
        self._value += 10
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = self._value
        return FetchResponse(response_mock)


class ConfigCacheMock(ConfigCache):
    def get(self):
        return TEST_OBJECT

    def set(self, value):
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
