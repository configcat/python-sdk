import json
import logging
import unittest
import time
import datetime
import requests

from configcatclient import PollingMode
from configcatclient.configcatoptions import Hooks
from configcatclient.configentry import ConfigEntry
from configcatclient.configfetcher import FetchResponse, ConfigFetcher
from configcatclient.configservice import ConfigService
from configcatclient.constants import VALUE
from configcatclient.logger import Logger
from configcatclient.utils import get_seconds_since_epoch, get_utc_now_seconds_since_epoch

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

from configcatclient.configcache import NullConfigCache
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, TEST_JSON, SingleValueConfigCache, \
    TEST_OBJECT

logging.basicConfig()
log = Logger('configcat', Hooks())


class LazyLoadingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.lazy_load(0), Hooks(), config_fetcher, log, config_cache, False)
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        cache_policy.close()

    def test_get(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.lazy_load(1), Hooks(), config_fetcher, log, config_cache, False)

        # Get value from Config Store, which indicates a config_fetcher call
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)

        # Get value from Config Store, which doesn't indicate a config_fetcher call (cache)
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)

        # Get value from Config Store, which indicates a config_fetcher call - 1 sec cache TTL
        time.sleep(1)
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.close()

    def test_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.lazy_load(160), Hooks(), config_fetcher, log, config_cache, False)

        # Get value from Config Store, which indicates a config_fetcher call
        settings, fetch_time = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)

        with mock.patch('configcatclient.utils.get_utc_now_seconds_since_epoch') as mock_get_utc_now_since_epoch:
            # assume 160 seconds has elapsed since the last call enough to do a
            # force refresh
            mock_get_utc_now_since_epoch.return_value = fetch_time + 161
            # Get value from Config Store, which indicates a config_fetcher call after cache invalidation
            cache_policy.refresh()
            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testKey').get(VALUE))
            self.assertEqual(config_fetcher.get_call_count, 2)
            cache_policy.close()

    def test_get_skips_hitting_api_after_update_from_different_thread(self):
        config_fetcher = mock.MagicMock()
        successful_fetch_response = FetchResponse.success(ConfigEntry(json.loads(TEST_JSON), '', TEST_JSON))
        config_fetcher.get_configuration.return_value = successful_fetch_response
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.lazy_load(160), Hooks(), config_fetcher, log, config_cache, False)

        # Get value from Config Store, which indicates a config_fetcher call
        with mock.patch('configcatclient.utils.get_utc_now') as mock_get_utc_now:
            now = datetime.datetime(2020, 5, 20, 0, 0, 0)
            mock_get_utc_now.return_value = now
            successful_fetch_response.entry.fetch_time = get_seconds_since_epoch(now)
            cache_policy.get_settings()
            self.assertEqual(config_fetcher.get_configuration.call_count, 1)
            # when the cache timeout is still within the limit skip any network
            # requests, as this could be that multiple threads have attempted
            # to acquire the lock at the same time, but only really one needs to update
            successful_fetch_response.entry.fetch_time = get_seconds_since_epoch(now - datetime.timedelta(seconds=159))
            cache_policy.get_settings()
            self.assertEqual(config_fetcher.get_configuration.call_count, 1)
            successful_fetch_response.entry.fetch_time = get_seconds_since_epoch(now - datetime.timedelta(seconds=161))
            cache_policy.get_settings()
            self.assertEqual(config_fetcher.get_configuration.call_count, 2)

    def test_error(self):
        config_fetcher = ConfigFetcherWithErrorMock('error')
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.lazy_load(160), Hooks(), config_fetcher, log, config_cache, False)

        # Get value from Config Store, which indicates a config_fetcher call
        settings, _ = cache_policy.get_settings()
        self.assertEqual(settings, None)
        cache_policy.close()

    def test_return_cached_config_when_cache_is_not_expired(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = SingleValueConfigCache(ConfigEntry(
            config=json.loads(TEST_JSON),
            etag='test-etag',
            config_json_string=TEST_JSON,
            fetch_time=get_utc_now_seconds_since_epoch()).serialize()
        )

        cache_policy = ConfigService('', PollingMode.lazy_load(1), Hooks(), config_fetcher, log, config_cache, False)

        settings, _ = cache_policy.get_settings()

        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 0)
        self.assertEqual(config_fetcher.get_fetch_count, 0)

        time.sleep(1)

        settings, _ = cache_policy.get_settings()

        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

    def test_fetch_config_when_cache_is_expired(self):
        config_fetcher = ConfigFetcherMock()
        cache_time_to_live_seconds = 1
        config_cache = SingleValueConfigCache(ConfigEntry(
            config=json.loads(TEST_JSON),
            etag='test-etag',
            config_json_string=TEST_JSON,
            fetch_time=get_utc_now_seconds_since_epoch() - cache_time_to_live_seconds).serialize()
        )

        cache_policy = ConfigService(
            '',
            PollingMode.lazy_load(cache_time_to_live_seconds),
            Hooks(),
            config_fetcher,
            log,
            config_cache,
            False
        )

        settings, _ = cache_policy.get_settings()

        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

    def test_online_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.lazy_load(cache_refresh_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode,
                                         Hooks(), config_fetcher, log, NullConfigCache(), False)

            self.assertFalse(cache_policy.is_offline())
            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))
            self.assertEqual(1, request_get.call_count)

            cache_policy.set_offline()
            self.assertTrue(cache_policy.is_offline())

            time.sleep(1.5)

            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))
            self.assertEqual(1, request_get.call_count)

            cache_policy.set_online()
            self.assertFalse(cache_policy.is_offline())

            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))
            self.assertEqual(2, request_get.call_count)

            cache_policy.close()

    def test_init_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.lazy_load(cache_refresh_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode,
                                         Hooks(), config_fetcher, log, NullConfigCache(), True)

            self.assertTrue(cache_policy.is_offline())
            settings, _ = cache_policy.get_settings()
            self.assertIsNone(settings)
            self.assertEqual(0, request_get.call_count)

            time.sleep(1.5)

            settings, _ = cache_policy.get_settings()
            self.assertIsNone(settings)
            self.assertEqual(0, request_get.call_count)

            cache_policy.set_online()
            self.assertFalse(cache_policy.is_offline())

            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))
            self.assertEqual(1, request_get.call_count)

            cache_policy.close()


if __name__ == '__main__':
    unittest.main()
