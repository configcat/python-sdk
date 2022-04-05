import logging
import unittest

from configcatclient import ConfigCatClientException
from configcatclient.configcatclient import ConfigCatClient
from configcatclienttests.mocks import ConfigCacheMock

logging.basicConfig(level=logging.INFO)


class ConfigCatClientTests(unittest.TestCase):
    def test_without_sdk_key(self):
        try:
            ConfigCatClient(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_bool(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual(True, client.get_value('testBoolKey', False))
        client.stop()

    def test_string(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual('testValue', client.get_value('testStringKey', 'default'))
        client.stop()

    def test_int(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual(1, client.get_value('testIntKey', 0))
        client.stop()

    def test_double(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual(1.1, client.get_value('testDoubleKey', 0.0))
        client.stop()

    def test_unknown(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual('default', client.get_value('testUnknownKey', 'default'))
        client.stop()

    def test_invalidation(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual(True, client.get_value('testBoolKey', False))
        client.stop()

    def test_get_all_keys(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        # Two list should have exactly the same elements, order doesn't matter.
        self.assertEqual({'testBoolKey', 'testStringKey', 'testIntKey', 'testDoubleKey', 'key1', 'key2'},
                         set(client.get_all_keys()))
        client.stop()

    def test_get_all_values(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        all_values = client.get_all_values()
        # Two dictionary should have exactly the same elements, order doesn't matter.
        self.assertEqual(6, len(all_values))
        self.assertEqual(True, all_values['testBoolKey'])
        self.assertEqual('testValue', all_values['testStringKey'])
        self.assertEqual(1, all_values['testIntKey'])
        self.assertEqual(1.1, all_values['testDoubleKey'])
        self.assertTrue(all_values['key1'])
        self.assertFalse(all_values['key2'])
        client.stop()


if __name__ == '__main__':
    unittest.main()
