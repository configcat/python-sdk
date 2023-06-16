import json
import logging
import unittest

from configcatclient import ConfigCatClient, ConfigCatOptions, PollingMode
from configcatclient.configcache import InMemoryConfigCache
from configcatclient.configcatoptions import Hooks
from configcatclient.configentry import ConfigEntry
from configcatclient.configservice import ConfigService
from configcatclient.utils import get_utc_now_seconds_since_epoch
from configcatclienttests.mocks import TEST_JSON, SingleValueConfigCache, HookCallbacks, TEST_JSON_FORMAT, TEST_SDK_KEY

logging.basicConfig()


class ConfigCacheTests(unittest.TestCase):

    def test_cache(self):
        config_store = InMemoryConfigCache()

        value = config_store.get('key')
        self.assertEqual(value, None)

        config_store.set('key', TEST_JSON)
        value = config_store.get('key')
        self.assertEqual(value, TEST_JSON)

        value2 = config_store.get('key2')
        self.assertEqual(value2, None)

    def test_cache_key(self):
        self.assertEqual("7f845c43ecc95e202b91e271435935e6d1391e5d", ConfigService._get_cache_key('test1'))
        self.assertEqual("a78b7e323ef543a272c74540387566a22415148a", ConfigService._get_cache_key('test2'))

    def test_cache_payload(self):
        now_seconds = 1686756435.8449
        etag = 'test-etag'
        entry = ConfigEntry(json.loads(TEST_JSON), etag, TEST_JSON, now_seconds)
        self.assertEqual('1686756435844' + '\n' + etag + '\n' + TEST_JSON, entry.serialize())

    def test_invalid_cache_content(self):
        hook_callbacks = HookCallbacks()
        hooks = Hooks(on_error=hook_callbacks.on_error)
        config_json_string = TEST_JSON_FORMAT.format(value='{"s": "test"}')
        config_cache = SingleValueConfigCache(ConfigEntry(
            config=json.loads(config_json_string),
            etag='test-etag',
            config_json_string=config_json_string,
            fetch_time=get_utc_now_seconds_since_epoch()).serialize()
        )

        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=config_cache,
                                                                    hooks=hooks))

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertEqual(0, hook_callbacks.error_call_count)

        # Invalid fetch time in cache
        config_cache._value = '\n'.join(['text',
                                         'test-etag',
                                         TEST_JSON_FORMAT.format(value='{"s": "test2"}')])

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertTrue('Error occurred while reading the cache.\nInvalid fetch time: text' in hook_callbacks.error)

        # Number of values is fewer than expected
        config_cache._value = '\n'.join([str(get_utc_now_seconds_since_epoch()),
                                         TEST_JSON_FORMAT.format(value='{"s": "test2"}')])

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertTrue('Error occurred while reading the cache.\nNumber of values is fewer than expected.'
                        in hook_callbacks.error)

        # Invalid config JSON
        config_cache._value = '\n'.join([str(get_utc_now_seconds_since_epoch()),
                                         'test-etag',
                                         'wrong-json'])

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertTrue('Error occurred while reading the cache.\nInvalid config JSON: wrong-json.'
                        in hook_callbacks.error)

        client.close()


if __name__ == '__main__':
    unittest.main()
