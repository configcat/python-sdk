import logging
import unittest
import time
import datetime
from requests import HTTPError

from configcatclient.configfetcher import FetchResponse
from configcatclient.utils import get_seconds_since_epoch, get_utc_now_seconds_since_epoch

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock

from configcatclient.configcache import InMemoryConfigCache
from configcatclient.lazyloadingcachepolicy import LazyLoadingCachePolicy
from configcatclienttests.mocks import ConfigFetcherMock, ConfigFetcherWithErrorMock, TEST_JSON

logging.basicConfig()
cache_key = 'cache_key'


class LazyLoadingCachePolicyTests(unittest.TestCase):
    def test_wrong_params(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 0)
        config = cache_policy.get()
        self.assertEqual(config, TEST_JSON)
        cache_policy.stop()

    def test_cache(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)

        # Get value from Config Store, which doesn't indicate a config_fetcher call (cache)
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
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)

        with mock.patch('configcatclient.utils.get_utc_now') as mock_get_utc_now:
            # assume 160 seconds has elapsed since the last call enough to do a 
            # force refresh
            mock_get_utc_now.return_value = cache_policy._last_updated + datetime.timedelta(seconds=161)
            # Get value from Config Store, which indicates a config_fetcher call after cache invalidation
            cache_policy.force_refresh()
            value = cache_policy.get()
            self.assertEqual(value, TEST_JSON)
            self.assertEqual(config_fetcher.get_call_count, 2)
            cache_policy.stop()

    def test_force_refresh(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 1)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

        time.sleep(1.2)
        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 2)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

        try:
            # Clear the cache
            cache_policy._lock.acquire_write()
            cache_policy._config_cache.set(cache_key, None)
        finally:
            cache_policy._lock.release_write()

        value = cache_policy.get()
        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 3)
        self.assertEqual(config_fetcher.get_fetch_count, 2)
        cache_policy.stop()

    def test_force_refresh_not_modified_config(self):
        config_fetcher = mock.MagicMock()
        successful_fetch_response = mock.MagicMock()
        successful_fetch_response.is_fetched.return_value = True
        successful_fetch_response.json.return_value = {FetchResponse.CONFIG: TEST_JSON}
        not_modified_fetch_response = mock.MagicMock()
        not_modified_fetch_response.is_fetched.return_value = False
        config_fetcher.get_configuration_json.return_value = successful_fetch_response
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        with mock.patch('configcatclient.utils.get_utc_now') as mock_get_utc_now:
            now = datetime.datetime(2020, 5, 20, 0, 0, 0)
            mock_get_utc_now.return_value = now
            successful_fetch_response.json.return_value[FetchResponse.FETCH_TIME] = get_seconds_since_epoch(now)
            value = cache_policy.get()
            self.assertEqual(mock_get_utc_now.call_count, 2)
            self.assertEqual(value, TEST_JSON)
            self.assertEqual(successful_fetch_response.json.call_count, 1)
            config_fetcher.get_configuration_json.return_value = not_modified_fetch_response
            new_time = datetime.datetime(2020, 5, 20, 0, 0, 0) + datetime.timedelta(seconds=161)
            mock_get_utc_now.return_value = new_time
            cache_policy.force_refresh()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 2)
            # this indicates that is_fetched() was correctly called and
            # the setting of the new last updated didn't occur
            self.assertEqual(not_modified_fetch_response.json.call_count, 0)
        cache_policy.stop()

    def test_get_skips_hitting_api_after_update_from_different_thread(self):
        config_fetcher = mock.MagicMock()
        successful_fetch_response = mock.MagicMock()
        successful_fetch_response.is_fetched.return_value = True
        successful_fetch_response.json.return_value = {FetchResponse.CONFIG: TEST_JSON}
        config_fetcher.get_configuration_json.return_value = successful_fetch_response
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        with mock.patch('configcatclient.utils.get_utc_now') as mock_get_utc_now:
            now = datetime.datetime(2020, 5, 20, 0, 0, 0)
            mock_get_utc_now.return_value = now
            successful_fetch_response.json.return_value[FetchResponse.FETCH_TIME] = get_seconds_since_epoch(now)
            cache_policy.get()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 1)
            # when the cache timeout is still within the limit skip any network
            # requests, as this could be that multiple threads have attempted
            # to acquire the lock at the same time, but only really one needs to update
            successful_fetch_response.json.return_value[FetchResponse.FETCH_TIME] = get_seconds_since_epoch(
                now - datetime.timedelta(seconds=159))
            cache_policy.get()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 1)
            successful_fetch_response.json.return_value[FetchResponse.FETCH_TIME] = get_seconds_since_epoch(
                now - datetime.timedelta(seconds=161))
            cache_policy.get()
            self.assertEqual(config_fetcher.get_configuration_json.call_count, 2)

    def test_http_error(self):
        config_fetcher = ConfigFetcherWithErrorMock(HTTPError("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_exception(self):
        config_fetcher = ConfigFetcherWithErrorMock(Exception("error"))
        config_cache = InMemoryConfigCache()
        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 160)

        # Get value from Config Store, which indicates a config_fetcher call
        value = cache_policy.get()
        self.assertEqual(value, None)
        cache_policy.stop()

    def test_return_cached_config_when_cache_is_not_expired(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        config_cache.set(cache_key, {
            FetchResponse.CONFIG: TEST_JSON,
            FetchResponse.FETCH_TIME: get_utc_now_seconds_since_epoch()
        })

        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, 1)

        value = cache_policy.get()

        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 0)
        self.assertEqual(config_fetcher.get_fetch_count, 0)

        time.sleep(1)

        value = cache_policy.get()

        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)

    def test_fetch_config_when_cache_is_expired(self):
        config_fetcher = ConfigFetcherMock()
        config_cache = InMemoryConfigCache()
        cache_time_to_live_seconds = 1
        config_cache.set(cache_key, {
            FetchResponse.CONFIG: TEST_JSON,
            FetchResponse.FETCH_TIME: get_utc_now_seconds_since_epoch() - cache_time_to_live_seconds
        })

        cache_policy = LazyLoadingCachePolicy(config_fetcher, config_cache, cache_key, cache_time_to_live_seconds)

        value = cache_policy.get()

        self.assertEqual(value, TEST_JSON)
        self.assertEqual(config_fetcher.get_call_count, 1)
        self.assertEqual(config_fetcher.get_fetch_count, 1)


if __name__ == '__main__':
    unittest.main()
