import logging
import unittest

from configcatclient.configcatclient import ConfigCatClient
from configcatclienttests.mocks import ConfigCacheMock
from configcatclient.configcatoptions import ConfigCatOptions
from configcatclient.pollingmode import PollingMode

logging.basicConfig(level=logging.INFO)


class VariationIdTests(unittest.TestCase):
    def test_get_variation_id(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual('fakeId1', client.get_value_details('key1', None).variation_id)
        self.assertEqual('fakeId2', client.get_value_details('key2', None).variation_id)
        client.close()

    def test_get_variation_id_not_found(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual(None, client.get_value_details('nonexisting', 'default_value').variation_id)
        client.close()

    def test_get_variation_id_empty_config(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual(None, client.get_value_details('nonexisting', 'default_value').variation_id)
        client.close()

    def test_get_all_variation_ids(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        result = [details.variation_id for details in client.get_all_value_details() if details.variation_id is not None]
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
