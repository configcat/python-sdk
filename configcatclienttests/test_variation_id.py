import logging
import unittest

from configcatclient.configcache import InMemoryConfigCache
from configcatclient.configcatclient import ConfigCatClient
from configcatclienttests.mocks import ConfigCacheMock

logging.basicConfig(level=logging.INFO)


class VariationIdTests(unittest.TestCase):
    def test_get_variation_id(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual('fakeId1', client.get_variation_id('key1', None))
        self.assertEqual('fakeId2', client.get_variation_id('key2', None))
        client.stop()

    def test_get_variation_id_not_found(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual('default_variation_id', client.get_variation_id('nonexisting', 'default_variation_id'))
        client.stop()

    def test_get_variation_id_empty_config(self):
        client = ConfigCatClient('test', 0, 0, None, 0)
        self.assertEqual('default_variation_id', client.get_variation_id('nonexisting', 'default_variation_id'))
        client.stop()

    def test_get_all_variation_ids(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        result = client.get_all_variation_ids()
        self.assertEqual(2, len(result))
        self.assertEqual('fakeId1', result[0])
        self.assertEqual('fakeId2', result[1])
        client.stop()

    def test_get_key_and_value(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        result = client.get_key_and_value('fakeId1')
        self.assertEqual('key1', result.key)
        self.assertTrue(result.value)
        result = client.get_key_and_value('fakeId2')
        self.assertEqual('key2', result.key)
        self.assertFalse(result.value)
        client.stop()

    def test_get_key_and_value_not_found(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        result = client.get_key_and_value('nonexisting')
        self.assertIsNone(result)
        client.stop()

    def test_get_key_and_value_empty_config(self):
        client = ConfigCatClient('test', 0, 0, None, 0)
        result = client.get_key_and_value('nonexisting')
        self.assertIsNone(result)
        client.stop()


if __name__ == '__main__':
    unittest.main()
