import logging
import unittest
import requests

from configcatclient import ConfigCatClientException
from configcatclient.configcatclient import ConfigCatClient
from configcatclient.user import User
from configcatclient.configcatoptions import ConfigCatOptions
from configcatclient.pollingmode import PollingMode
from configcatclienttests.mocks import ConfigCacheMock, TEST_OBJECT

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

logging.basicConfig(level=logging.INFO)


class ConfigCatClientTests(unittest.TestCase):
    def test_ensure_singleton_per_sdk_key(self):
        client1 = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        client2 = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

        self.assertEqual(client1, client2)

        ConfigCatClient.close_all()

        client1 = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

        self.assertNotEqual(client1, client2)

        ConfigCatClient.close_all()

    def test_without_sdk_key(self):
        try:
            ConfigCatClient(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_bool(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual(True, client.get_value('testBoolKey', False))
        client.close()

    def test_string(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual('testValue', client.get_value('testStringKey', 'default'))
        client.close()

    def test_int(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual(1, client.get_value('testIntKey', 0))
        client.close()

    def test_double(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual(1.1, client.get_value('testDoubleKey', 0.0))
        client.close()

    def test_unknown(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual('default', client.get_value('testUnknownKey', 'default'))
        client.close()

    def test_invalidation(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        self.assertEqual(True, client.get_value('testBoolKey', False))
        client.close()

    def test_get_all_keys(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        # Two list should have exactly the same elements, order doesn't matter.
        self.assertEqual({'testBoolKey', 'testStringKey', 'testIntKey', 'testDoubleKey', 'key1', 'key2'},
                         set(client.get_all_keys()))
        client.close()

    def test_get_all_values(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        all_values = client.get_all_values()
        # Two dictionary should have exactly the same elements, order doesn't matter.
        self.assertEqual(6, len(all_values))
        self.assertEqual(True, all_values['testBoolKey'])
        self.assertEqual('testValue', all_values['testStringKey'])
        self.assertEqual(1, all_values['testIntKey'])
        self.assertEqual(1.1, all_values['testDoubleKey'])
        self.assertTrue(all_values['key1'])
        self.assertFalse(all_values['key2'])
        client.close()

    def test_cache_key(self):
        client1 = ConfigCatClient.get('test1', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                config_cache=ConfigCacheMock()))
        client2 = ConfigCatClient.get('test2', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                config_cache=ConfigCacheMock()))
        self.assertEqual("5a9acc8437104f46206f6f273c4a5e26dd14715c", client1._ConfigCatClient__get_cache_key())
        self.assertEqual("ade7f71ba5d52ebd3d9aeef5f5488e6ffe6323b8", client2._ConfigCatClient__get_cache_key())
        client1.close()
        client2.close()

    def test_default_user_get_value(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        self.assertEqual("fake1", client.get_value("testStringKey", ""))
        self.assertEqual("fake2", client.get_value("testStringKey", "", user2))

        client.clear_default_user()
        self.assertEqual("testValue", client.get_value("testStringKey", ""))

        client.close()

    def test_default_user_get_all_value(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
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

        client.close()

    def test_default_user_get_variation_id(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        self.assertEqual("id1", client.get_variation_id("testStringKey", ""))
        self.assertEqual("id2", client.get_variation_id("testStringKey", "", user2))

        client.clear_default_user()
        self.assertEqual("id", client.get_variation_id("testStringKey", ""))

        client.close()

    def test_default_user_get_all_variation_ids(self):
        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock()))
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

        client.close()

    def test_online_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

            self.assertFalse(client.is_offline())

            client.force_refresh()

            self.assertEqual(1, request_get.call_count)

            client.set_offline()
            self.assertTrue(client.is_offline())

            client.force_refresh()

            self.assertEqual(1, request_get.call_count)

            client.set_online()
            self.assertFalse(client.is_offline())

            client.force_refresh()

            self.assertEqual(2, request_get.call_count)

            client.close()

    def test_init_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                  offline=True))

            self.assertTrue(client.is_offline())

            client.force_refresh()

            self.assertEqual(0, request_get.call_count)

            client.set_online()
            self.assertFalse(client.is_offline())

            client.force_refresh()

            self.assertEqual(1, request_get.call_count)

            client.close()


if __name__ == '__main__':
    unittest.main()
