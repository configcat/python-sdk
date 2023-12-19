import json
import time
import logging

from configcatclient.config import SettingType
from configcatclient.configentry import ConfigEntry
from configcatclient.utils import get_utc_now_seconds_since_epoch, distant_past

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


from configcatclient.configfetcher import FetchResponse, ConfigFetcher
from configcatclient.interfaces import ConfigCache

TEST_SDK_KEY = 'configcat-sdk-test-key/0000000000000000000000'
TEST_SDK_KEY1 = 'configcat-sdk-test-key/0000000000000000000001'
TEST_SDK_KEY2 = 'configcat-sdk-test-key/0000000000000000000002'

TEST_JSON = r'''{
   "p": {
       "u": "https://cdn-global.configcat.com",
       "r": 0
   },
   "f": {
       "testKey": { "v": { "s": "testValue" }, "t": 1 }
   }
}'''

TEST_JSON_FORMAT = '{{ "f": {{ "testKey": {{ "t": {value_type}, "v": {value}, "p": [], "r": [] }} }} }}'

TEST_JSON2 = r'''{
  "p": {
       "u": "https://cdn-global.configcat.com",
       "r": 0
  },
  "f": {
      "testKey": { "v": { "s": "testValue" }, "t": 1 },
      "testKey2": { "v": { "s": "testValue2" }, "t": 1 }
  }
}'''

TEST_OBJECT = json.loads(r'''{
  "p": {
    "u": "https://cdn-global.configcat.com",
    "r": 0
  },
  "s": [
    {"n": "id1", "r": [{"a": "Identifier", "c": 2, "l": ["@test1.com"]}]},
    {"n": "id2", "r": [{"a": "Identifier", "c": 2, "l": ["@test2.com"]}]}
  ],
  "f": {
    "testBoolKey": {"v": {"b": true}, "t": 0},
    "testStringKey": {"v": {"s": "testValue"}, "i": "id", "t": 1, "r": [
      {"c": [{"s": {"s": 0, "c": 0}}], "s": {"v": {"s": "fake1"}, "i": "id1"}},
      {"c": [{"s": {"s": 1, "c": 0}}], "s": {"v": {"s": "fake2"}, "i": "id2"}}
    ]},
    "testIntKey": {"v": {"i": 1}, "t": 2},
    "testDoubleKey": {"v": {"d": 1.1}, "t": 3},
    "key1": {"v": {"b": true}, "t": 0, "i": "id3"},
    "key2": {"v": {"s": "fake4"}, "t": 1, "i": "id4",
      "r": [
        {"c": [{"s": {"s": 0, "c": 0}}], "p": [
          {"p": 50, "v": {"s": "fake5"}, "i": "id5"}, {"p": 50, "v": {"s": "fake6"}, "i": "id6"}
        ]}
      ], 
      "p": [
        {"p": 50, "v": {"s": "fake7"}, "i": "id7"}, {"p": 50, "v": {"s": "fake8"}, "i": "id8"}
      ]
    }
  }
}''')


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
                ConfigEntry(json.loads(self._configuration), self._etag, self._configuration, get_utc_now_seconds_since_epoch())
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
        return FetchResponse.failure(self._error, True)


class ConfigFetcherWaitMock(ConfigFetcher):
    def __init__(self, wait_seconds):
        self._wait_seconds = wait_seconds

    def get_configuration(self, etag=''):
        time.sleep(self._wait_seconds)
        return FetchResponse.success(ConfigEntry(json.loads(TEST_JSON), etag, TEST_JSON))


class ConfigFetcherCountMock(ConfigFetcher):
    def __init__(self):
        self._value = 0

    def get_configuration(self, etag=''):
        self._value += 1
        value_string = '{ "i": %s }' % self._value
        config_json_string = TEST_JSON_FORMAT.format(value_type=SettingType.INT, value=value_string)
        config = json.loads(config_json_string)
        return FetchResponse.success(ConfigEntry(config, etag, config_json_string))


class ConfigCacheMock(ConfigCache):
    def get(self, key):
        return '\n'.join([str(distant_past), 'test-etag', json.dumps(TEST_OBJECT)])

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
        if name == 'ETag':
            return self.etag
        return None


class MockResponse:
    def __init__(self, json_data, status_code, etag=None):
        self.json_data = json_data
        self.text = json.dumps(json_data)
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


class MockLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(MockLogHandler, self).__init__(*args, **kwargs)
        self.error_logs = []
        self.warning_logs = []
        self.info_logs = []

    def clear(self):
        self.error_logs = []
        self.warning_logs = []
        self.info_logs = []

    def emit(self, record):
        if record.levelno == logging.ERROR:
            self.error_logs.append(record.getMessage())
        elif record.levelno == logging.WARNING:
            self.warning_logs.append(record.getMessage())
        elif record.levelno == logging.INFO:
            self.info_logs.append(record.getMessage())
