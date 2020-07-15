import logging
import unittest
import time
import datetime
from requests import HTTPError

try:
    from unittest import mock
except ImportError:
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

        with mock.patch('configcatclient.lazyloadingcachepolicy.datetime') as mock_datetime:
            # assume 160 seconds has elapsed since the last call enough to do a 
            # force refresh
            mock_datetime.datetime.utcnow.return_value = cache_policy._last_updated + datetime.timedelta(seconds=161)
            # Get value from Config Store, which indicates a config_fetcher call after cache invalidation
            cache_policy.force_refresh()
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

        try:
            # Clear the cache
            cache_policy._lock.acquire_write()
            cache_policy._config_cache.set(None)
        finally:
            cache_policy._lock.release_write()

        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 2)
        cache_policy.stop()

    def test_force_refresh_not_modified_config(self):
        config_fetcher = mock.MagicMock()
        successful_fetch_response = mock.MagicMock()
        successful_fetch_response.is_fetched.return_value = True
        successful_fetch_response.json.return_value = TEST_JSON
        not_modified_fetch_response = mock.MagicMock()
        not_modified_fetch_response.is_fetched.return_value = False
        config_fetcher.get_configuration_json.return_value = successful_fetch_response
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        with mock.patch('configcatclient.lazyloadingcachepolicy.datetime') as mock_datetime:
            mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 5, 20, 0, 0, 0)
            value = cache_policy.get()
            self.assertEqual(mock_datetime.datetime.utcnow.call_count, 2)
            self.assertEqual(value, TEST_JSON)
            self.assertEqual(successful_fetch_response.json.call_count, 1)
            config_fetcher.get_configuration_json.return_value = not_modified_fetch_response
            new_time = datetime.datetime(2020, 5, 20, 0, 0, 0) + datetime.timedelta(seconds=161)
            mock_datetime.datetime.utcnow.return_value = new_time
            cache_policy.force_refresh()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 2)
            # this indicates that is_fetched() was correctly called and
            # the setting of the new last updated didn't occur
            self.assertEqual(not_modified_fetch_response.json.call_count, 0)
            self.assertEqual(mock_datetime.datetime.utcnow.call_count, 3)
            # last updated should still be set in the case of a 304
            self.assertEqual(cache_policy._last_updated, new_time)
        cache_policy.stop()

    def test_get_skips_hitting_api_after_update_from_different_thread(self):
        config_fetcher = mock.MagicMock()
        successful_fetch_response = mock.MagicMock()
        successful_fetch_response.is_fetched.return_value = True
        successful_fetch_response.json.return_value = TEST_JSON
        config_fetcher.get_configuration_json.return_value = successful_fetch_response
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        with mock.patch('configcatclient.lazyloadingcachepolicy.datetime') as mock_datetime:
            now = datetime.datetime(2020, 5, 20, 0, 0, 0)
            mock_datetime.datetime.utcnow.return_value = now
            self.assertIsNone(cache_policy._last_updated)
            cache_policy.get()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 1)
            # when the cache timeout is still within the limit skip any network
            # requests, as this could be that multiple threads have attempted
            # to acquire the lock at the same time, but only really one needs to update
            cache_policy._last_updated = now - datetime.timedelta(seconds=159)
            cache_policy.get()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 1)
            cache_policy._last_updated = now - datetime.timedelta(seconds=161)
            cache_policy.get()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 2)

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
