import json
import time

from configcatclient.interfaces import ConfigFetcher, ConfigCache

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

    def get_configuration_json(self):
        self._call_count = self._call_count + 1
        return self._configuration

    def set_configuration_json(self, value):
        self._configuration = value

    def close(self):
        pass

    @property
    def get_call_count(self):
        return self._call_count


class ConfigFetcherWithErrorMock(ConfigFetcher):

    def __init__(self, exception):
        self._exception = exception

    def get_configuration_json(self):
        raise self._exception

    def close(self):
        pass


class ConfigFetcherWaitMock(ConfigFetcher):

    def __init__(self, wait_seconds):
        self._wait_seconds = wait_seconds

    def get_configuration_json(self):
        time.sleep(self._wait_seconds)
        return TEST_JSON

    def close(self):
        pass


class ConfigFetcherCountMock(ConfigFetcher):

    def __init__(self):
        self._value = 0

    def get_configuration_json(self):
        self._value += 10
        return self._value

    def close(self):
        pass


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
