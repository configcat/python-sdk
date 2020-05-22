import logging
import unittest
import time
import datetime
from requests import HTTPError
import mock

from configcatclient.configcache import InMemoryConfigCache
from configcatclient.lazyloadingcachepolicy import LazyLoadingCachePolicy
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, TEST_JSON
from configcatclient.configfetcher import FetchResponse

logging.basicConfig()


class LazyLoadingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 0)
        config = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_cache(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 1)

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
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 160)

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

    def test_force_refresh_honours_304(self):
        config_fetcher = mock.MagicMock()
        successful_response = mock.MagicMock()
        successful_response.status_code = 200
        successful_response.json.return_value = TEST_JSON
        not_modified_response = mock.MagicMock()
        not_modified_response.status_code = 304
        not_modified_response.json.side_effect = ValueError("this response contains no body")
        config_fetcher.get_configuration_json.return_value = FetchResponse(successful_response)
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        with mock.patch('configcatclient.lazyloadingcachepolicy.datetime') as mock_datetime:
            mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 5, 20, 0, 0, 0)
            value = cache_policy.get()
            self.assertEqual(mock_datetime.datetime.utcnow.call_count, 2)
            self.assertEqual(value, TEST_JSON)
            self.assertEqual(successful_response.json.call_count, 1)
            config_fetcher.get_configuration_json.return_value = FetchResponse(not_modified_response)
            cache_policy.force_refresh()
            self.assertEqual(value, TEST_JSON)
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 2)
            # this indicates that is_fetched() was correctly called and
            # the setting of the new last updated didn't occur
            self.assertEqual(not_modified_response.json.call_count, 0)
        cache_policy.stop()

    def test_http_error(self):
        config_fetcher = ConfigFetcherWithErrorMock(HTTPError("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_exception(self):
        config_fetcher = ConfigFetcherWithErrorMock(Exception("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()


if __name__ == '__main__':
    unittest.main()
