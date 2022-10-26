import logging
import unittest

from configcatclient.configcache import InMemoryConfigCache
from configcatclient.configcatclient import ConfigCatClient
from configcatclienttests.mocks import ConfigCacheMock
from configcatclient.configcatoptions import ConfigCatOptions
from configcatclient.pollingmode import PollingMode

logging.basicConfig(level=logging.INFO)


class VariationIdTests(unittest.TestCase):
    def test_get_variation_id(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual('fakeId1', client.get_variation_id('key1', None))
        self.assertEqual('fakeId2', client.get_variation_id('key2', None))
        client.close()

    def test_get_variation_id_not_found(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual('default_variation_id', client.get_variation_id('nonexisting', 'default_variation_id'))
        client.close()

    def test_get_variation_id_empty_config(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual('default_variation_id', client.get_variation_id('nonexisting', 'default_variation_id'))
        client.close()

    def test_get_all_variation_ids(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        result = client.get_all_variation_ids()
        self.assertEqual(3, len(result))
        self.assertTrue('id' in result)
        self.assertTrue('fakeId1' in result)
        self.assertTrue('fakeId2' in result)
        client.close()

    def test_get_key_and_value(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        result = client.get_key_and_value('fakeId1')
        self.assertEqual('key1', result.key)
        self.assertTrue(result.value)
        result = client.get_key_and_value('fakeId2')
        self.assertEqual('key2', result.key)
        self.assertFalse(result.value)
        client.close()

    def test_get_key_and_value_not_found(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        result = client.get_key_and_value('nonexisting')
        self.assertIsNone(result)
        client.close()

    def test_get_key_and_value_empty_config(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        result = client.get_key_and_value('nonexisting')
        self.assertIsNone(result)
        client.close()


if __name__ == '__main__':
    unittest.main()
