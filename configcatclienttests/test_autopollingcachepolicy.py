import logging
import unittest
import time
from requests import HTTPError

from configcatclient.autopollingcachepolicy import AutoPollingCachePolicy
from configcatclient.configcache import InMemoryConfigCache
from configcatclient.configcatoptions import Hooks
from configcatclient.configfetcher import FetchResponse
from configcatclient.utils import get_utc_now_seconds_since_epoch
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, ConfigFetcherWaitMock, \
    ConfigFetcherCountMock, TEST_JSON, CallCounter, TEST_JSON2

logging.basicConfig()
log = logging.getLogger()
cache_key = 'cache_key'


class AutoPollingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 0, -1, None)
        time.sleep(2)
        config, _ = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_init_wait_time_ok(self):
        config_fetcher = ConfigFetcherWaitMock(0)
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 60, 5, None)
        config, _ = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_init_wait_time_timeout(self):
        config_fetcher = ConfigFetcherWaitMock(5)
        config_cache = InMemoryConfigCache()
        start_time = time.time()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 60, 1, None)
        config, _ = cache_policy.get()
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.assertEqual(config, None)
        self.assertTrue(elapsed_time > 1)
        self.assertTrue(elapsed_time < 2)
        cache_policy.stop()

    def test_fetch_call_count(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 1, None)
        time.sleep(3)
        self.assertEqual(config_fetcher.get_call_count, 2)
        config, _ = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_updated_values(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 5, None)
        config, _ = cache_policy.get()
        self.assertEqual(config, 10)
        time.sleep(2.200)
        config, _ = cache_policy.get()
        self.assertEqual(config, 20)
        cache_policy.stop()

    def test_http_error(self):
        config_fetcher = ConfigFetcherWithErrorMock(HTTPError("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 60, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value, _ = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_exception(self):
        config_fetcher = ConfigFetcherWithErrorMock(Exception("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 60, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value, _ = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_stop(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 5, None)
        cache_policy.stop()
        config, _ = cache_policy.get()
        self.assertEqual(config, 10)
        time.sleep(2.200)
        config, _ = cache_policy.get()
        self.assertEqual(config, 10)
        cache_policy.stop()

    def test_rerun(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 5, None)
        time.sleep(2.200)
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.stop()

    def test_callback(self):
        call_counter = CallCounter()
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 5, call_counter.callback)
        time.sleep(1)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(call_counter.get_call_count, 1)
        time.sleep(1.2)
        self.assertEqual(config_fetcher.get_call_count, 2)
        self.assertEqual(call_counter.get_call_count, 1)
        config_fetcher.set_configuration_json(TEST_JSON2)
        time.sleep(2.2)
        self.assertEqual(config_fetcher.get_call_count, 3)
        self.assertEqual(call_counter.get_call_count, 2)
        cache_policy.stop()

    def test_callback_exception(self):
        call_counter = CallCounter()
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 5, call_counter.callback_exception)
        time.sleep(1)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(call_counter.get_call_count, 1)
        time.sleep(1.2)
        self.assertEqual(config_fetcher.get_call_count, 2)
        self.assertEqual(call_counter.get_call_count, 1)
        config_fetcher.set_configuration_json(TEST_JSON2)
        time.sleep(2.2)
        self.assertEqual(config_fetcher.get_call_count, 3)
        self.assertEqual(call_counter.get_call_count, 2)
        cache_policy.stop()

    def test_refetch_config(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(), 2, 1, None)
        time.sleep(1.5)

        config, _ = cache_policy.get()

        self.assertEqual(config, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

        time.sleep(1.5)
        config, _ = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 2)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

        try:
            # Clear the cache
            cache_policy._lock.acquire_write()
            cache_policy._config_cache.set(cache_key, None)
        finally:
            cache_policy._lock.release_write()

        time.sleep(1.5)
        self.assertEqual(config_fetcher.get_call_count, 3)
        self.assertEqual(config_fetcher.get_fetch_count, 2)
        config, _ = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_return_cached_config_when_cache_is_not_expired(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        poll_interval_seconds = 2
        max_init_wait_time_seconds = 1
        config_cache.set(cache_key, {
            FetchResponse.CONFIG: TEST_JSON,
            FetchResponse.FETCH_TIME: get_utc_now_seconds_since_epoch()
        })

        start_time = time.time()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(),
                                              poll_interval_seconds, max_init_wait_time_seconds, None)

        config, _ = cache_policy.get()
        elapsed_time = time.time() - start_time

        # max init wait time should be ignored when cache is not expired
        self.assertLessEqual(elapsed_time, max_init_wait_time_seconds)

        self.assertEqual(config, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 0)
        self.assertEqual(config_fetcher.get_fetch_count, 0)

        time.sleep(3)

        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

    def test_fetch_config_when_cache_is_expired(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        poll_interval_seconds = 2
        max_init_wait_time_seconds = 1
        config_cache.set(cache_key, {
            FetchResponse.CONFIG: TEST_JSON,
            FetchResponse.FETCH_TIME: get_utc_now_seconds_since_epoch() - poll_interval_seconds
        })
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(),
                                              poll_interval_seconds, max_init_wait_time_seconds, None)

        config, _ = cache_policy.get()

        self.assertEqual(config, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

    def test_init_wait_time_return_cached(self):
        config_fetcher = ConfigFetcherWaitMock(5)
        config_cache = InMemoryConfigCache()
        poll_interval_seconds = 60
        max_init_wait_time_seconds = 1
        config_cache.set(cache_key, {
            FetchResponse.CONFIG: TEST_JSON2,
            FetchResponse.FETCH_TIME: get_utc_now_seconds_since_epoch() - 2 * poll_interval_seconds
        })

        start_time = time.time()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, cache_key, log, Hooks(),
                                              poll_interval_seconds, max_init_wait_time_seconds, None)

        config, _ = cache_policy.get()
        elapsed_time = time.time() - start_time

        self.assertGreater(elapsed_time, max_init_wait_time_seconds)
        self.assertLess(elapsed_time, max_init_wait_time_seconds + 1)
        self.assertEqual(config, TEST_JSON2)


if __name__ == '__main__':
    unittest.main()
