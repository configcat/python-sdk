import logging
import unittest
import time
from requests import HTTPError

from configcatclient.autopollingcachepolicy import AutoPollingCachePolicy
from configcatclient.configcache import InMemoryConfigCache
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, ConfigFetcherWaitMock, \
    ConfigFetcherCountMock, TEST_JSON, CallCounter, TEST_JSON2

logging.basicConfig()


class AutoPollingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 0, -1, None)
        time.sleep(2)
        config = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_init_wait_time_ok(self):
        config_fetcher = ConfigFetcherWaitMock(0)
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 60, 5, None)
        config = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_init_wait_time_timeout(self):
        config_fetcher = ConfigFetcherWaitMock(5)
        config_cache = InMemoryConfigCache()
        start_time = time.time()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 60, 1, None)
        config = cache_policy.get()
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.assertEqual(config, None)
        self.assertTrue(elapsed_time > 1)
        self.assertTrue(elapsed_time < 2)
        cache_policy.stop()

    def test_fetch_call_count(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 2, 1, None)
        time.sleep(3)
        self.assertEqual(config_fetcher.get_call_count, 2)
        config = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_updated_values(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 2, 5, None)
        config = cache_policy.get()
        self.assertEqual(config, 10)
        time.sleep(2.200)
        config = cache_policy.get()
        self.assertEqual(config, 20)
        cache_policy.stop()

    def test_http_error(self):
        config_fetcher = ConfigFetcherWithErrorMock(HTTPError("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 60, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_exception(self):
        config_fetcher = ConfigFetcherWithErrorMock(Exception("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 60, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_stop(self):
        config_fetcher = ConfigFetcherCountMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 2, 5, None)
        cache_policy.stop()
        config = cache_policy.get()
        self.assertEqual(config, 10)
        time.sleep(2.200)
        config = cache_policy.get()
        self.assertEqual(config, 10)
        cache_policy.stop()

    def test_rerun(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 2, 5, None)
        time.sleep(2.200)
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.stop()

    def test_callback(self):
        call_counter = CallCounter()
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 2, 5, call_counter.callback)
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
        cache_policy = AutoPollingCachePolicy(config_fetcher, config_cache, 2, 5, call_counter.callback_exception)
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


if __name__ == '__main__':
    unittest.main()
