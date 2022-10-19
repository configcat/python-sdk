import logging
import unittest

from configcatclient import ConfigCatClientException
from configcatclient.configcatclient import ConfigCatClient
from configcatclient.user import User
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

    def test_cache_key(self):
        client1 = ConfigCatClient('test1', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        client2 = ConfigCatClient('test2', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        self.assertEqual("5a9acc8437104f46206f6f273c4a5e26dd14715c", client1._ConfigCatClient__get_cache_key())
        self.assertEqual("ade7f71ba5d52ebd3d9aeef5f5488e6ffe6323b8", client2._ConfigCatClient__get_cache_key())
        client1.stop()
        client2.stop()

    def test_default_user_get_value(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        self.assertEqual("fake1", client.get_value("testStringKey", ""))
        self.assertEqual("fake2", client.get_value("testStringKey", "", user2))

        client.clear_default_user()
        self.assertEqual("testValue", client.get_value("testStringKey", ""))

        client.stop()

    def test_default_user_get_all_value(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        all_values = client.get_all_values()
        # Two dictionary should have exactly the same elements, order doesn't matter.
        self.assertEqual(6, len(all_values))
        self.assertEqual(True, all_values['testBoolKey'])
        self.assertEqual('fake1', all_values['testStringKey'])
        self.assertEqual(1, all_values['testIntKey'])
        self.assertEqual(1.1, all_values['testDoubleKey'])
        self.assertTrue(all_values['key1'])
        self.assertFalse(all_values['key2'])

        all_values = client.get_all_values(user2)
        # Two dictionary should have exactly the same elements, order doesn't matter.
        self.assertEqual(6, len(all_values))
        self.assertEqual(True, all_values['testBoolKey'])
        self.assertEqual('fake2', all_values['testStringKey'])
        self.assertEqual(1, all_values['testIntKey'])
        self.assertEqual(1.1, all_values['testDoubleKey'])
        self.assertTrue(all_values['key1'])
        self.assertFalse(all_values['key2'])

        client.clear_default_user()
        all_values = client.get_all_values()
        self.assertEqual(6, len(all_values))
        self.assertEqual(True, all_values['testBoolKey'])
        self.assertEqual('testValue', all_values['testStringKey'])
        self.assertEqual(1, all_values['testIntKey'])
        self.assertEqual(1.1, all_values['testDoubleKey'])
        self.assertTrue(all_values['key1'])
        self.assertFalse(all_values['key2'])

        client.stop()

    def test_default_user_get_variation_id(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        self.assertEqual("id1", client.get_variation_id("testStringKey", ""))
        self.assertEqual("id2", client.get_variation_id("testStringKey", "", user2))

        client.clear_default_user()
        self.assertEqual("id", client.get_variation_id("testStringKey", ""))

        client.stop()

    def test_default_user_get_all_variation_ids(self):
        client = ConfigCatClient('test', 0, 0, None, 0, config_cache_class=ConfigCacheMock)
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        result = client.get_all_variation_ids()
        self.assertEqual(3, len(result))
        self.assertTrue('id1' in result)
        self.assertTrue('fakeId1' in result)
        self.assertTrue('fakeId2' in result)

        result = client.get_all_variation_ids(user2)
        self.assertEqual(3, len(result))
        self.assertTrue('id2' in result)
        self.assertTrue('fakeId1' in result)
        self.assertTrue('fakeId2' in result)

        client.clear_default_user()
        result = client.get_all_variation_ids()
        self.assertEqual(3, len(result))
        self.assertTrue('id' in result)
        self.assertTrue('fakeId1' in result)
        self.assertTrue('fakeId2' in result)

        client.stop()


if __name__ == '__main__':
    unittest.main()
