import logging
import unittest

from configcatclient.configcatclient import ConfigCatClient
from configcatclienttests.mocks import ConfigCacheMock, TEST_SDK_KEY
from configcatclient.configcatoptions import ConfigCatOptions
from configcatclient.pollingmode import PollingMode

logging.basicConfig(level=logging.INFO)


class VariationIdTests(unittest.TestCase):
    def test_get_variation_id(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual('id3', client.get_value_details('key1', None).variation_id)
        self.assertEqual('id4', client.get_value_details('key2', None).variation_id)
        client.close()

    def test_get_variation_id_not_found(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual(None, client.get_value_details('nonexisting', 'default_value').variation_id)
        client.close()

    def test_get_variation_id_empty_config(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual(None, client.get_value_details('nonexisting', 'default_value').variation_id)
        client.close()

    def test_get_key_and_value(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        result = client.get_key_and_value('id1')
        self.assertEqual('testStringKey', result.key)
        self.assertEqual('fake1', result.value)

        result = client.get_key_and_value('id2')
        self.assertEqual('testStringKey', result.key)
        self.assertEqual('fake2', result.value)

        result = client.get_key_and_value('id3')
        self.assertEqual('key1', result.key)
        self.assertTrue(result.value)

        result = client.get_key_and_value('id4')
        self.assertEqual('key2', result.key)
        self.assertEqual('fake4', result.value)

        result = client.get_key_and_value('id5')
        self.assertEqual('key2', result.key)
        self.assertEqual('fake5', result.value)

        result = client.get_key_and_value('id6')
        self.assertEqual('key2', result.key)
        self.assertEqual('fake6', result.value)

        result = client.get_key_and_value('id7')
        self.assertEqual('key2', result.key)
        self.assertEqual('fake7', result.value)

        result = client.get_key_and_value('id8')
        self.assertEqual('key2', result.key)
        self.assertEqual('fake8', result.value)

        client.close()

    def test_get_key_and_value_not_found(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        result = client.get_key_and_value('nonexisting')
        self.assertIsNone(result)
        client.close()

    def test_get_key_and_value_empty_config(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        result = client.get_key_and_value('nonexisting')
        self.assertIsNone(result)
        client.close()


if __name__ == '__main__':
    unittest.main()
