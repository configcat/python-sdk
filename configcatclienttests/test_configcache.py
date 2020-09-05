import logging
import unittest

from configcatclient.configcache import InMemoryConfigCache
from configcatclienttests.mocks import TEST_JSON

logging.basicConfig()


class ConfigCacheTests(unittest.TestCase):

    def test_cache(self):
        config_store = InMemoryConfigCache()

        value = config_store.get('key')
        self.assertEqual(value, None)

        config_store.set('key', TEST_JSON)
        value = config_store.get('key')
        self.assertEqual(value, TEST_JSON)


if __name__ == '__main__':
    unittest.main()
