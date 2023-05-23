import logging
import unittest
from os import path
import tempfile
import json
import time

from configcatclient import ConfigCatClient
from configcatclient.localdictionarydatasource import LocalDictionaryFlagOverrides
from configcatclient.localfiledatasource import LocalFileFlagOverrides
from configcatclient.overridedatasource import OverrideBehaviour
from configcatclienttests.mocks import MockResponse, TEST_SDK_KEY
from configcatclient.configcatoptions import ConfigCatOptions
from configcatclient.pollingmode import PollingMode

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

logging.basicConfig()


def mocked_requests_get(*args, **kwargs):
    return MockResponse({"f": {"fakeKey": {"v": {"b": False}}, "fakeKey2": {"v": {"s": "test"}}}}, 200)


class OverrideTests(unittest.TestCase):
    script_dir = path.dirname(__file__)

    def test_file(self):
        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalFileFlagOverrides(
                                       file_path=path.join(OverrideTests.script_dir, 'test.json'),
                                       override_behaviour=OverrideBehaviour.LocalOnly))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)

        self.assertTrue(client.get_value('enabledFeature', False))
        self.assertFalse(client.get_value('disabledFeature', True))
        self.assertEqual(5, client.get_value('intSetting', 0))
        self.assertEqual(3.14, client.get_value('doubleSetting', 0.0))
        self.assertEqual('test', client.get_value('stringSetting', ''))
        client.close()

    def test_simple_file(self):
        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalFileFlagOverrides(
                                       file_path=path.join(OverrideTests.script_dir, 'test-simple.json'),
                                       override_behaviour=OverrideBehaviour.LocalOnly))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)

        self.assertTrue(client.get_value('enabledFeature', False))
        self.assertFalse(client.get_value('disabledFeature', True))
        self.assertEqual(5, client.get_value('intSetting', 0))
        self.assertEqual(3.14, client.get_value('doubleSetting', 0.0))
        self.assertEqual('test', client.get_value('stringSetting', ''))
        client.close()

    def test_non_existent_file(self):
        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalFileFlagOverrides(
                                       file_path='non_existent.json',
                                       override_behaviour=OverrideBehaviour.LocalOnly))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)
        self.assertFalse(client.get_value('enabledFeature', False))
        client.close()

    def test_reload_file(self):
        temp = tempfile.NamedTemporaryFile(mode="w")
        dictionary = {'flags': {
            'enabledFeature': False
        }}
        json.dump(dictionary, temp)
        temp.flush()

        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalFileFlagOverrides(
                                       file_path=temp.name,
                                       override_behaviour=OverrideBehaviour.LocalOnly))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)

        self.assertFalse(client.get_value('enabledFeature', True))

        time.sleep(0.5)

        # clear the content of the temp file
        temp.seek(0)
        temp.truncate()

        # change the temporary file
        dictionary['flags']['enabledFeature'] = True
        json.dump(dictionary, temp)
        temp.flush()

        self.assertTrue(client.get_value('enabledFeature', False))

        client.close()

    def test_invalid_file(self):
        temp = tempfile.NamedTemporaryFile(mode="w")
        temp.write('{"flags": {"enabledFeature": true}')
        temp.flush()

        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalFileFlagOverrides(
                                       file_path=temp.name,
                                       override_behaviour=OverrideBehaviour.LocalOnly))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)

        self.assertFalse(client.get_value('enabledFeature', False))

        client.close()

    def test_dictionary(self):
        dictionary = {
            'enabledFeature': True,
            'disabledFeature': False,
            'intSetting': 5,
            'doubleSetting': 3.14,
            'stringSetting': 'test'
        }

        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalDictionaryFlagOverrides(
                                       source=dictionary,
                                       override_behaviour=OverrideBehaviour.LocalOnly))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)

        self.assertTrue(client.get_value('enabledFeature', False))
        self.assertFalse(client.get_value('disabledFeature', True))
        self.assertEqual(5, client.get_value('intSetting', 0))
        self.assertEqual(3.14, client.get_value('doubleSetting', 0.0))
        self.assertEqual('test', client.get_value('stringSetting', ''))
        client.close()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_local_over_remote(self, mock_get):
        dictionary = {
            'fakeKey': True,
            'nonexisting': True
        }

        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalDictionaryFlagOverrides(
                                       source=dictionary,
                                       override_behaviour=OverrideBehaviour.LocalOverRemote))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)
        client.force_refresh()

        self.assertTrue(client.get_value('fakeKey', False))
        self.assertEqual('test', client.get_value('fakeKey2', 'default'))
        self.assertTrue(client.get_value('nonexisting', False))
        client.close()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_remote_over_local(self, mock_get):
        dictionary = {
            'fakeKey': True,
            'nonexisting': True
        }

        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalDictionaryFlagOverrides(
                                       source=dictionary,
                                       override_behaviour=OverrideBehaviour.RemoteOverLocal))
        client = ConfigCatClient.get(sdk_key=TEST_SDK_KEY, options=options)
        client.force_refresh()

        self.assertFalse(client.get_value('fakeKey', True))
        self.assertEqual('test', client.get_value('fakeKey2', 'default'))
        self.assertTrue(client.get_value('nonexisting', False))
        client.close()


if __name__ == '__main__':
    unittest.main()
