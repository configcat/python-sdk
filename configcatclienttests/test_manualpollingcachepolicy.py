import json
import logging
import unittest
import requests

from configcatclient import PollingMode
from configcatclient.configcache import NullConfigCache, InMemoryConfigCache
from configcatclient.configcatoptions import Hooks
from configcatclient.configfetcher import ConfigFetcher
from configcatclient.configservice import ConfigService
from configcatclient.constants import VALUE, FEATURE_FLAGS, STRING_VALUE
from configcatclient.logger import Logger
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, TEST_OBJECT, TEST_JSON_FORMAT

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

logging.basicConfig()
log = Logger('configcat', Hooks())
cache_key = 'cache_key'


class ManualPollingCachePolicyTests(unittest.TestCase):
    def test_without_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.manual_poll(), Hooks(), config_fetcher, log, config_cache, False)
        config, _ = cache_policy.get_config()
        self.assertEqual(config, None)
        self.assertEqual(config_fetcher.get_call_count, 0)
        cache_policy.close()

    def test_with_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.manual_poll(), Hooks(), config_fetcher, log, config_cache, False)
        cache_policy.refresh()
        config, _ = cache_policy.get_config()
        settings = config.get(FEATURE_FLAGS)
        self.assertEqual('testValue', settings.get('testKey').get(VALUE).get(STRING_VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)
        cache_policy.close()

    def test_with_refresh_error(self):
        config_fetcher = ConfigFetcherWithErrorMock('error')
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.manual_poll(), Hooks(), config_fetcher, log, config_cache, False)
        cache_policy.refresh()
        config, _ = cache_policy.get_config()
        self.assertEqual(config, None)
        cache_policy.close()

    def test_with_failed_refresh(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.manual_poll()
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode, Hooks(), config_fetcher, log, NullConfigCache(), False)

            cache_policy.refresh()
            config, _ = cache_policy.get_config()
            settings = config.get(FEATURE_FLAGS)
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE).get(STRING_VALUE))

            response_mock.json.return_value = {}
            response_mock.status_code = 500
            response_mock.headers = {}

            cache_policy.refresh()
            config, _ = cache_policy.get_config()
            settings = config.get(FEATURE_FLAGS)
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE).get(STRING_VALUE))

            cache_policy.close()

    def test_cache(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = json.loads(TEST_JSON_FORMAT.format(value='{ "s": "test"}'))
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.manual_poll()
            config_cache = InMemoryConfigCache()
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode, Hooks(), config_fetcher, log, config_cache, False)

            cache_policy.refresh()
            config, _ = cache_policy.get_config()
            settings = config.get(FEATURE_FLAGS)
            self.assertEqual('test', settings.get('testKey').get(VALUE).get(STRING_VALUE))
            self.assertEqual(1, request_get.call_count)
            self.assertEqual(1, len(config_cache._value))

            response_mock.json.return_value = json.loads(TEST_JSON_FORMAT.format(value='{ "s": "test2"}'))

            cache_policy.refresh()
            config, _ = cache_policy.get_config()
            settings = config.get(FEATURE_FLAGS)
            self.assertEqual('test2', settings.get('testKey').get(VALUE).get(STRING_VALUE))
            self.assertEqual(2, request_get.call_count)
            self.assertEqual(1, len(config_cache._value))

            cache_policy.close()

    def test_online_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.manual_poll()
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode, Hooks(), config_fetcher, log, NullConfigCache(), False)

            self.assertFalse(cache_policy.is_offline())
            self.assertTrue(cache_policy.refresh().is_success)
            config, _ = cache_policy.get_config()
            settings = config.get(FEATURE_FLAGS)
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE).get(STRING_VALUE))
            self.assertEqual(1, request_get.call_count)

            cache_policy.set_offline()

            self.assertTrue(cache_policy.is_offline())
            self.assertFalse(cache_policy.refresh().is_success)
            self.assertEqual(1, request_get.call_count)

            cache_policy.set_online()

            self.assertFalse(cache_policy.is_offline())
            self.assertTrue(cache_policy.refresh().is_success)
            self.assertEqual(2, request_get.call_count)

            cache_policy.close()

    def test_init_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.manual_poll()
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode, Hooks(), config_fetcher, log, NullConfigCache(), True)

            self.assertTrue(cache_policy.is_offline())
            self.assertFalse(cache_policy.refresh().is_success)
            self.assertEqual(0, request_get.call_count)

            cache_policy.set_online()

            self.assertFalse(cache_policy.is_offline())
            self.assertTrue(cache_policy.refresh().is_success)
            config, _ = cache_policy.get_config()
            settings = config.get(FEATURE_FLAGS)
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE).get(STRING_VALUE))
            self.assertEqual(1, request_get.call_count)

            cache_policy.close()


if __name__ == '__main__':
    unittest.main()
