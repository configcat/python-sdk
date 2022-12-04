import json
import logging
import unittest
import time
import requests

from configcatclient import PollingMode
from configcatclient.configcache import InMemoryConfigCache, NullConfigCache
from configcatclient.configcatoptions import Hooks
from configcatclient.configentry import ConfigEntry
from configcatclient.configfetcher import FetchResponse, ConfigFetcher
from configcatclient.configservice import ConfigService
from configcatclient.constants import VALUE
from configcatclient.utils import get_utc_now_seconds_since_epoch
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, ConfigFetcherWaitMock, \
    ConfigFetcherCountMock, TEST_JSON, TEST_JSON2, HookCallbacks, SingleValueConfigCache, TEST_OBJECT

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
log = logging.getLogger()


class AutoPollingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()

        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=0,
                                                               max_init_wait_time_seconds=-1),
                                     Hooks(), config_fetcher, log, config_cache, False)
        time.sleep(2)
        config, _ = cache_policy.get_settings()
        self.assertEqual('testValue', config.get('testKey').get(VALUE))
        cache_policy.close()

    def test_init_wait_time_ok(self):
        config_fetcher = ConfigFetcherWaitMock(0)
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=60,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        config, _ = cache_policy.get_settings()
        self.assertEqual('testValue', config.get('testKey').get(VALUE))
        cache_policy.close()

    def test_init_wait_time_timeout(self):
        config_fetcher = ConfigFetcherWaitMock(5)
        config_cache = NullConfigCache()
        start_time = time.time()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=60,
                                                               max_init_wait_time_seconds=1),
                                     Hooks(), config_fetcher, log, config_cache, False)
        config, _ = cache_policy.get_settings()
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.assertEqual(config, None)
        self.assertTrue(elapsed_time > 1)
        self.assertTrue(elapsed_time < 2)
        cache_policy.close()

    def test_fetch_call_count(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=1),
                                     Hooks(), config_fetcher, log, config_cache, False)
        time.sleep(3)
        self.assertEqual(config_fetcher.get_call_count, 2)
        config, _ = cache_policy.get_settings()
        self.assertEqual('testValue', config.get('testKey').get(VALUE))
        cache_policy.close()

    def test_updated_values(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        config, _ = cache_policy.get_settings()
        self.assertEqual(1, config.get('testKey').get(VALUE))
        time.sleep(2.200)
        config, _ = cache_policy.get_settings()
        self.assertEqual(2, config.get('testKey').get(VALUE))
        cache_policy.close()

    def test_error(self):
        config_fetcher = ConfigFetcherWithErrorMock('error')
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=60,
                                                               max_init_wait_time_seconds=1),
                                     Hooks(), config_fetcher, log, config_cache, False)

        # Get value from Config Store, which indicates a config_fetcher call
        value, _ = cache_policy.get_settings()
        self.assertEqual(value, None)
        cache_policy.close()

    def test_close(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=2,
                                                               max_init_wait_time_seconds=5),
                                     Hooks(), config_fetcher, log, config_cache, False)
        cache_policy.close()
        config, _ = cache_policy.get_settings()
        self.assertEqual(1, config.get('testKey').get(VALUE))
        time.sleep(2.200)
        config, _ = cache_policy.get_settings()
        self.assertEqual(1, config.get('testKey').get(VALUE))
        cache_policy.close()

    def test_rerun(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = NullConfigCache()
        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=2,
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

        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=2,
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

        cache_policy = ConfigService('', PollingMode.auto_poll(auto_poll_interval_seconds=2,
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

        config, _ = cache_policy.get_settings()
        elapsed_time = time.time() - start_time

        # max init wait time should be ignored when cache is not expired
        self.assertLessEqual(elapsed_time, max_init_wait_time_seconds)

        self.assertEqual('testValue', config.get('testKey').get(VALUE))
        self.assertEqual(config_fetcher.get_call_count, 0)
        self.assertEqual(config_fetcher.get_fetch_count, 0)

        time.sleep(3)

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

        config, _ = cache_policy.get_settings()

        self.assertEqual('testValue', config.get('testKey').get(VALUE))
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

        config, _ = cache_policy.get_settings()
        elapsed_time = time.time() - start_time

        self.assertGreater(elapsed_time, max_init_wait_time_seconds)
        self.assertLess(elapsed_time, max_init_wait_time_seconds + 1)
        self.assertEqual('testValue', config.get('testKey').get(VALUE))
        self.assertEqual('testValue2', config.get('testKey2').get(VALUE))
        cache_policy.close()

    def test_online_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {'Etag': 'test-etag'}

            polling_mode = PollingMode.auto_poll(auto_poll_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())
            cache_policy = ConfigService('', polling_mode,
                                         Hooks(), config_fetcher, log, NullConfigCache(), False)

            self.assertFalse(cache_policy.is_offline())

            time.sleep(1.5)

            cache_policy.set_offline()
            self.assertTrue(cache_policy.is_offline())
            self.assertEqual(2, request_get.call_count)

            time.sleep(2)

            self.assertEqual(2, request_get.call_count)
            cache_policy.set_online()
            self.assertFalse(cache_policy.is_offline())

            time.sleep(1)

            self.assertEqual(3, request_get.call_count)
            cache_policy.close()

    def test_init_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {'Etag': 'test-etag'}

            polling_mode = PollingMode.auto_poll(auto_poll_interval_seconds=1)
            config_fetcher = ConfigFetcher('', log, polling_mode.identifier())

            cache_policy = ConfigService('', polling_mode,
                                         Hooks(), config_fetcher, log, NullConfigCache(), True)

            self.assertTrue(cache_policy.is_offline())
            self.assertEqual(0, request_get.call_count)

            time.sleep(2)

            self.assertEqual(0, request_get.call_count)
            cache_policy.set_online()
            self.assertFalse(cache_policy.is_offline())

            time.sleep(2.5)

            self.assertGreaterEqual(request_get.call_count, 2)
            cache_policy.close()


if __name__ == '__main__':
    unittest.main()
