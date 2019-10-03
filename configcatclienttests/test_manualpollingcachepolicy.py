import logging
import unittest
from requests import HTTPError

from configcatclient.configcache import InMemoryConfigCache
from configcatclient.logger import ConfigCatConsoleLogger
from configcatclient.manualpollingcachepolicy import ManualPollingCachePolicy
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, TEST_JSON

logging.basicConfig()


class ManualPollingCachePolicyTests(unittest.TestCase):
    def test_without_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = ManualPollingCachePolicy(config_fetcher, config_cache, logger)
        value = cache_policy.get()
        self.assertEqual(value, None)
        self.assertEqual(config_fetcher.get_call_count, 0)
        cache_policy.stop()

    def test_with_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = ManualPollingCachePolicy(config_fetcher, config_cache, logger)
        cache_policy.force_refresh()
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)
        cache_policy.stop()

    def test_with_refresh_httperror(self):
        config_fetcher = ConfigFetcherWithErrorMock(HTTPError("error"))
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = ManualPollingCachePolicy(config_fetcher, config_cache, logger)
        cache_policy.force_refresh()
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_with_refresh_exception(self):
        config_fetcher = ConfigFetcherWithErrorMock(Exception("error"))
        config_cache = InMemoryConfigCache()
        logger = ConfigCatConsoleLogger()
        cache_policy = ManualPollingCachePolicy(config_fetcher, config_cache, logger)
        cache_policy.force_refresh()
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()


if __name__ == '__main__':
    unittest.main()
