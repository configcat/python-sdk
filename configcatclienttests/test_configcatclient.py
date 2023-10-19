import datetime
import json
import logging
import unittest

import pytest
import requests

from configcatclient import ConfigCatClientException
from configcatclient.configcatclient import ConfigCatClient
from configcatclient.configentry import ConfigEntry
from configcatclient.config import VALUE, SERVED_VALUE, STRING_VALUE
from configcatclient.user import User
from configcatclient.configcatoptions import ConfigCatOptions, Hooks
from configcatclient.pollingmode import PollingMode
from configcatclient.utils import get_utc_now, get_utc_now_seconds_since_epoch
from configcatclienttests.mocks import ConfigCacheMock, TEST_OBJECT, TEST_SDK_KEY, HookCallbacks, SingleValueConfigCache

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
logging.getLogger('configcat').setLevel(logging.INFO)


class ConfigCatClientTests(unittest.TestCase):
    def test_ensure_singleton_per_sdk_key(self):
        client1 = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        client2 = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

        self.assertEqual(client1, client2)

        ConfigCatClient.close_all()

        client1 = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

        self.assertNotEqual(client1, client2)

        ConfigCatClient.close_all()

    def test_without_sdk_key(self):
        try:
            ConfigCatClient(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_invalid_sdk_key(self):
        with pytest.raises(ConfigCatClientException):
            ConfigCatClient.get('key')

        with pytest.raises(ConfigCatClientException):
            ConfigCatClient.get('configcat-proxy/key')

        with pytest.raises(ConfigCatClientException):
            ConfigCatClient.get('1234567890abcdefghijkl01234567890abcdefghijkl')

        with pytest.raises(ConfigCatClientException):
            ConfigCatClient.get('configcat-sdk-2/1234567890abcdefghijkl/1234567890abcdefghijkl')

        with pytest.raises(ConfigCatClientException):
            ConfigCatClient.get('configcat/1234567890abcdefghijkl/1234567890abcdefghijkl')

        ConfigCatClient.get('1234567890abcdefghijkl/1234567890abcdefghijkl')
        ConfigCatClient.get('configcat-sdk-1/1234567890abcdefghijkl/1234567890abcdefghijkl')
        ConfigCatClient.get('configcat-proxy/key', options=ConfigCatOptions(base_url='base_url'))

    def test_bool(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual(True, client.get_value('testBoolKey', False))
        client.close()

    def test_string(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual('testValue', client.get_value('testStringKey', 'default'))
        client.close()

    def test_int(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual(1, client.get_value('testIntKey', 0))
        client.close()

    def test_double(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual(1.1, client.get_value('testDoubleKey', 0.0))
        client.close()

    def test_unknown(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual('default', client.get_value('testUnknownKey', 'default'))
        client.close()

    def test_invalidation(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        self.assertEqual(True, client.get_value('testBoolKey', False))
        client.close()

    def test_incorrect_json(self):
        config_json_string = r'''{
           "f": {
             "testKey":  {
               "t": 0,
               "r": [ {
                 "c": [ { "t": { "a": "Custom1", "c": 19, "d": "wrong_utc_timestamp" } } ],
                 "s": { "v": { "b": true } }
               } ],
               "v": { "b": false }
             }
           }
        }'''
        config_cache = SingleValueConfigCache(ConfigEntry(
            config=json.loads(config_json_string),
            etag='test-etag',
            config_json_string=config_json_string,
            fetch_time=get_utc_now_seconds_since_epoch()).serialize()
        )

        hook_callbacks = HookCallbacks()
        hooks = Hooks(
            on_error=hook_callbacks.on_error
        )
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=config_cache,
                                                                    hooks=hooks))
        self.assertEqual(False, client.get_value('testKey', False, User('1234', custom={'Custom1': 1681118000.56})))
        self.assertEqual(1, hook_callbacks.error_call_count)
        self.assertTrue(hook_callbacks.error.startswith("Failed to evaluate setting 'testKey'."))
        client.close()

    def test_get_all_keys(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        # Two list should have exactly the same elements, order doesn't matter.
        self.assertEqual({'testBoolKey', 'testStringKey', 'testIntKey', 'testDoubleKey', 'key1', 'key2'},
                         set(client.get_all_keys()))
        client.close()

    def test_get_all_values(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
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

    def test_get_all_value_details(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        all_details = client.get_all_value_details()

        def details_by_key(all_details, key):
            for details in all_details:
                if details.key == key:
                    return details
            return None

        self.assertEqual(6, len(all_details))
        details = details_by_key(all_details, 'testBoolKey')
        self.assertEqual('testBoolKey', details.key)
        self.assertEqual(True, details.value)

        details = details_by_key(all_details, 'testStringKey')
        self.assertEqual('testStringKey', details.key)
        self.assertEqual('testValue', details.value)
        self.assertEqual('id', details.variation_id)

        details = details_by_key(all_details, 'testIntKey')
        self.assertEqual('testIntKey', details.key)
        self.assertEqual(1, details.value)

        details = details_by_key(all_details, 'testDoubleKey')
        self.assertEqual('testDoubleKey', details.key)
        self.assertEqual(1.1, details.value)

        details = details_by_key(all_details, 'key1')
        self.assertEqual('key1', details.key)
        self.assertEqual(True, details.value)
        self.assertEqual('fakeId1', details.variation_id)

        details = details_by_key(all_details, 'key2')
        self.assertEqual('key2', details.key)
        self.assertEqual(False, details.value)
        self.assertEqual('fakeId2', details.variation_id)

        client.close()

    def test_get_value_details(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
            client.force_refresh()

            user = User('test@test1.com')
            details = client.get_value_details('testStringKey', '', user)

            self.assertEqual('fake1', details.value)
            self.assertEqual('testStringKey', details.key)
            self.assertEqual('id1', details.variation_id)
            self.assertFalse(details.is_default_value)
            self.assertIsNone(details.error)
            self.assertIsNone(details.matched_percentage_rule)
            self.assertEqual('fake1', details.matched_targeting_rule[SERVED_VALUE][VALUE][STRING_VALUE])
            self.assertEqual(str(user), str(details.user))
            now = get_utc_now()
            self.assertGreaterEqual(now, details.fetch_time)
            self.assertLessEqual(now, details.fetch_time + + datetime.timedelta(seconds=1))

            client.close()

    def test_default_user_get_value(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=ConfigCacheMock()))
        user1 = User("test@test1.com")
        user2 = User("test@test2.com")

        client.set_default_user(user1)
        self.assertEqual("fake1", client.get_value("testStringKey", ""))
        self.assertEqual("fake2", client.get_value("testStringKey", "", user2))

        client.clear_default_user()
        self.assertEqual("testValue", client.get_value("testStringKey", ""))

        client.close()

    def test_default_user_get_all_values(self):
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
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

    def test_online_offline(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

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

            client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
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
