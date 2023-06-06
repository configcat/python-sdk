import logging
import unittest

from configcatclient import ConfigCatClient, ConfigCatOptions, PollingMode
from configcatclient.configcache import InMemoryConfigCache
from configcatclient.configcatoptions import Hooks
from configcatclient.configfetcher import ConfigFetcher
from configcatclient.constants import VALUE
from configcatclient.logger import Logger
from configcatclient.configservice import ConfigService
from configcatclient.utils import get_utc_now_seconds_since_epoch, distant_future
from configcatclienttests.mocks import TEST_JSON, SingleValueConfigCache, HookCallbacks, TEST_JSON_FORMAT, \
    ConfigFetcherMock

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
        self.assertEqual("23c140ee52202e4ce7125714651f14b777caa40d", ConfigService._get_cache_key('test1'))
        self.assertEqual("ea7ecf506fe66ed3d4b667c81f9b96551a9d2112", ConfigService._get_cache_key('test2'))

    def test_invalid_cache_content(self):
        # TODO: Store the callback results in lists in HookCallbacks
        errors = []
        hooks = Hooks(on_error=lambda error: errors.append(error))

        config_cache = SingleValueConfigCache('\n'.join([str(get_utc_now_seconds_since_epoch()),
                                                         'test-etag',
                                                         TEST_JSON_FORMAT.format(value='"test"')]))

        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=config_cache,
                                                              hooks=hooks))

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertEqual(0, len(errors))

        # Invalid fetch time in cache
        config_cache._value = '\n'.join(['text',
                                         'test-etag',
                                         TEST_JSON_FORMAT.format(value='"test2"')])

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertTrue('Error occurred while reading the cache.\nInvalid fetch time: text' in errors)

        # Number of values is fewer than expected
        errors = []
        config_cache._value = '\n'.join([str(get_utc_now_seconds_since_epoch()),
                                         TEST_JSON_FORMAT.format(value='"test2"')])

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertTrue('Error occurred while reading the cache.\nNumber of values is fewer than expected.' in errors)

        # Invalid config JSON
        errors = []
        config_cache._value = '\n'.join([str(get_utc_now_seconds_since_epoch()),
                                         'test-etag',
                                         'wrong-json'])

        self.assertEqual('test', client.get_value('testKey', 'default'))
        self.assertTrue('Error occurred while reading the cache.\nInvalid config JSON: wrong-json. '
                        'Expecting value: line 1 column 1 (char 0)' in errors)

        client.close()


if __name__ == '__main__':
    unittest.main()
