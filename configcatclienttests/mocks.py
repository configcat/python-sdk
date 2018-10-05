import json
import time

from configcatclient.interfaces import ConfigFetcher, ConfigCache

TEST_JSON = '{"testKey": { "Value": "testValue", "SettingType": 1, ' \
            '"PercentageRolloutItems": [], "TargetedRolloutRules": [] }}'

TEST_JSON2 = '{"testKey": { "Value": "testValue", "SettingType": 1, ' \
             '"PercentageRolloutItems": [], "TargetedRolloutRules": [] }, ' \
             '"testKey2": { "Value": "testValue2", "SettingType": 1, ' \
             '"PercentageRolloutItems": [], "TargetedRolloutRules": [] }}'

TEST_OBJECT = json.loads(
    '{"testBoolKey": '
    '{"Value": true,"SettingType": 0, "PercentageRolloutItems": [],"TargetedRolloutRules": []},'
    '"testStringKey": '
    '{"Value": "testValue","SettingType": 1, "PercentageRolloutItems": [],"TargetedRolloutRules": []},'
    '"testIntKey": '
    '{"Value": 1,"SettingType": 2, "PercentageRolloutItems": [],"TargetedRolloutRules": []},'
    '"testDoubleKey": '
    '{"Value": 1.1,"SettingType": 3,"PercentageRolloutItems": [],"TargetedRolloutRules": []}}')


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
