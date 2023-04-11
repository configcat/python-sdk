import json
import logging
import unittest
import time
import requests

from unittest import mock
from unittest.mock import Mock

from configcatclient import PollingMode
from configcatclient.configcache import NullConfigCache
from configcatclient.configcatoptions import Hooks
from configcatclient.configentry import ConfigEntry
from configcatclient.configfetcher import ConfigFetcher
from configcatclient.configservice import ConfigService
from configcatclient.constants import VALUE
from configcatclient.utils import get_utc_now_seconds_since_epoch
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, ConfigFetcherWaitMock, \
    ConfigFetcherCountMock, TEST_JSON, TEST_JSON2, HookCallbacks, SingleValueConfigCache, TEST_OBJECT


logging.basicConfig()
log = logging.getLogger()


class AutoPollingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()

        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=0,
                                                               max_init_wait_time_seconds=-1),
                                     Hooks(), config_fetcher, log, config_cache, False)
        time.sleep(2)
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        cache_policy.close()

    def test_init_wait_time_ok(self):
        config_fetcher = ConfigFetcherWaitMock(0)
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=60,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        cache_policy.close()

    def test_init_wait_time_timeout(self):
        config_fetcher = ConfigFetcherWaitMock(5)
        config_cache = NullConfigCache()
        start_time = time.time()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=60,
                                                               max_init_wait_time_seconds=1),
                                     Hooks(), config_fetcher, log, config_cache, False)
        settings, _ = cache_policy.get_settings()
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.assertEqual(settings, None)
        self.assertTrue(elapsed_time > 1)
        self.assertTrue(elapsed_time < 2)
        cache_policy.close()

    def test_fetch_call_count(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=1),
                                     Hooks(), config_fetcher, log, config_cache, False)
        time.sleep(3)
        self.assertEqual(config_fetcher.get_call_count, 2)
        settings, _ = cache_policy.get_settings()
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        cache_policy.close()

    def test_updated_values(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        settings, _ = cache_policy.get_settings()
        self.assertEqual(1, settings.get('testKey').get(VALUE))
        time.sleep(2.200)
        settings, _ = cache_policy.get_settings()
        self.assertEqual(2, settings.get('testKey').get(VALUE))
        cache_policy.close()

    def test_error(self):
        config_fetcher = ConfigFetcherWithErrorMock('error')
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=60,
                                                               max_init_wait_time_seconds=1),
                                     Hooks(), config_fetcher, log, config_cache, False)

        # Get value from Config Store, which indicates a config_fetcher call
        settings, _ = cache_policy.get_settings()
        self.assertEqual(settings, None)
        cache_policy.close()

    def test_close(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        cache_policy.close()
        settings, _ = cache_policy.get_settings()
        self.assertEqual(1, settings.get('testKey').get(VALUE))
        time.sleep(2.200)
        settings, _ = cache_policy.get_settings()
        self.assertEqual(1, settings.get('testKey').get(VALUE))
        cache_policy.close()

    def test_rerun(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        time.sleep(2.200)
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.close()

    def test_callback(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        hook_callbacks = HookCallbacks()
        hooks = Hooks()
        hooks.add_on_config_changed(hook_callbacks.on_config_changed)

        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     hooks, config_fetcher, log, config_cache, False)
        time.sleep(1)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(hook_callbacks.changed_config_call_count, 1)
        time.sleep(1.2)
        self.assertEqual(config_fetcher.get_call_count, 2)
        self.assertEqual(hook_callbacks.changed_config_call_count, 1)
        config_fetcher.set_configuration_json(TEST_JSON2)
        time.sleep(2.2)
        self.assertEqual(config_fetcher.get_call_count, 3)
        self.assertEqual(hook_callbacks.changed_config_call_count, 2)
        cache_policy.close()

    def test_callback_exception(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        hook_callbacks = HookCallbacks()
        hooks = Hooks()
        hooks.add_on_config_changed(hook_callbacks.callback_exception)

        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     hooks, config_fetcher, log, config_cache, False)
        time.sleep(1)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(hook_callbacks.callback_exception_call_count, 1)
        time.sleep(1.2)
        self.assertEqual(config_fetcher.get_call_count, 2)
        self.assertEqual(hook_callbacks.callback_exception_call_count, 1)
        config_fetcher.set_configuration_json(TEST_JSON2)
        time.sleep(2.2)
        self.assertEqual(config_fetcher.get_call_count, 3)
        self.assertEqual(hook_callbacks.callback_exception_call_count, 2)
        cache_policy.close()

    def test_with_failed_refresh(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            polling_mode = PollingMode.auto_poll(poll_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode, Hooks(), config_fetcher, log, NullConfigCache(), False)

            # first call
            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))

            response_mock.json.return_value = {}
            response_mock.status_code = 500
            response_mock.headers = {}

            # wait for cache invalidation
            time.sleep(1.5)

            # previous value returned because of the refresh failure
            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))

            cache_policy.close()

    def test_return_cached_config_when_cache_is_not_expired(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = SingleValueConfigCache(json.dumps({
            ConfigEntry.CONFIG: json.loads(TEST_JSON),
            ConfigEntry.ETAG: 'test-etag',
            ConfigEntry.FETCH_TIME: get_utc_now_seconds_since_epoch()
        }))
        poll_interval_seconds = 2
        max_init_wait_time_seconds = 1

        start_time = time.time()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds,
                                                               max_init_wait_time_seconds),
                                     Hooks(), config_fetcher, log, config_cache, False)

        settings, _ = cache_policy.get_settings()
        elapsed_time = time.time() - start_time

        # max init wait time should be ignored when cache is not expired
        self.assertLessEqual(elapsed_time, max_init_wait_time_seconds)

        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 0)
        self.assertEqual(config_fetcher.get_fetch_count, 0)

        time.sleep(3)

        settings, _ = cache_policy.get_settings()

        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)
        cache_policy.close()

    def test_fetch_config_when_cache_is_expired(self):
        config_fetcher = ConfigFetcherMock()
        poll_interval_seconds = 2
        max_init_wait_time_seconds = 1
        config_cache = SingleValueConfigCache(json.dumps({
            ConfigEntry.CONFIG: json.loads(TEST_JSON),
            ConfigEntry.ETAG: 'test-etag',
            ConfigEntry.FETCH_TIME: get_utc_now_seconds_since_epoch() - poll_interval_seconds
        }))
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds,
                                                               max_init_wait_time_seconds),
                                     Hooks(), config_fetcher, log, config_cache, False)

        settings, _ = cache_policy.get_settings()

        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)
        cache_policy.close()

    def test_init_wait_time_return_cached(self):
        config_fetcher = ConfigFetcherWaitMock(5)
        poll_interval_seconds = 60
        max_init_wait_time_seconds = 1
        config_cache = SingleValueConfigCache(json.dumps({
            ConfigEntry.CONFIG: json.loads(TEST_JSON2),
            ConfigEntry.ETAG: 'test-etag',
            ConfigEntry.FETCH_TIME: get_utc_now_seconds_since_epoch() - 2 * poll_interval_seconds
        }))

        start_time = time.time()
        cache_policy = ConfigService('', PollingMode.auto_poll(poll_interval_seconds,
                                                               max_init_wait_time_seconds),
                                     Hooks(), config_fetcher, log, config_cache, False)

        settings, _ = cache_policy.get_settings()
        elapsed_time = time.time() - start_time

        self.assertGreater(elapsed_time, max_init_wait_time_seconds)
        self.assertLess(elapsed_time, max_init_wait_time_seconds + 1)
        self.assertEqual('testValue', settings.get('testKey').get(VALUE))
        self.assertEqual('testValue2', settings.get('testKey2').get(VALUE))
        cache_policy.close()

    def test_online_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {'Etag': 'test-etag'}

            polling_mode = PollingMode.auto_poll(poll_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode,
                                         Hooks(), config_fetcher, log, NullConfigCache(), False)

            self.assertFalse(cache_policy.is_offline())

            time.sleep(1.5)

            cache_policy.set_offline()
            self.assertTrue(cache_policy.is_offline())
            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))
            self.assertEqual(2, request_get.call_count)

            time.sleep(2)

            self.assertEqual(2, request_get.call_count)
            cache_policy.set_online()
            self.assertFalse(cache_policy.is_offline())

            time.sleep(1)

            self.assertGreaterEqual(request_get.call_count, 3)
            cache_policy.close()

    def test_init_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {'Etag': 'test-etag'}

            polling_mode = PollingMode.auto_poll(poll_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())

            cache_policy = ConfigService('', polling_mode,
                                         Hooks(), config_fetcher, log, NullConfigCache(), True)

            self.assertTrue(cache_policy.is_offline())
            settings, _ = cache_policy.get_settings()
            self.assertIsNone(settings)
            self.assertEqual(0, request_get.call_count)

            time.sleep(2)

            settings, _ = cache_policy.get_settings()
            self.assertIsNone(settings)
            self.assertEqual(0, request_get.call_count)

            cache_policy.set_online()
            self.assertFalse(cache_policy.is_offline())

            time.sleep(2.5)

            settings, _ = cache_policy.get_settings()
            self.assertEqual('testValue', settings.get('testStringKey').get(VALUE))
            self.assertGreaterEqual(request_get.call_count, 2)
            cache_policy.close()


if __name__ == '__main__':
    unittest.main()
