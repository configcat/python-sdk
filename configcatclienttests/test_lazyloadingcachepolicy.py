import logging
import unittest
import time
from requests import HTTPError

from configcatclient.configcache import InMemoryConfigCache
from configcatclient.lazyloadingcachepolicy import LazyLoadingCachePolicy
from configcatclient.logger import ConfigCatConsoleLogger
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, TEST_JSON

logging.basicConfig()


class LazyLoadingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, logger, 0)
        config = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_cache(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, logger, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)

        # Get value from Config Store, which doesn't indicates a config_fetcher call (cache)
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)

        # Get value from Config Store, which indicates a config_fetcher call - 1 sec cache TTL
        time.sleep(1)
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.stop()

    def test_force_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, logger, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)

        # Get value from Config Store, which indicates a config_fetcher call after cache invalidation
        cache_policy.force_refresh()
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.stop()

    def test_http_error(self):
        config_fetcher = ConfigFetcherWithErrorMock(HTTPError("error"))
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, logger, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_exception(self):
        config_fetcher = ConfigFetcherWithErrorMock(Exception("error"))
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, logger, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()


if __name__ == '__main__':
    unittest.main()
