import logging
import unittest

from configcatclient import ConfigCatClient
from configcatclient.localdictionarydatasource import LocalDictionaryDataSource
from configcatclient.overridedatasource import OverrideBehaviour
from configcatclienttests.mocks import MockResponse

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
    return MockResponse({"f": {"fakeKey": {"v": False}}}, 200)


class LocalTests(unittest.TestCase):
    TEST_JSON_FORMAT = '{ "f": { "fakeKey": { "v": {value}, "p": [], "r": [] } } }'

    def test_dictionary(self):
        dictionary = {
            'enabledFeature': True,
            'disabledFeature': False,
            'intSetting': 5,
            'doubleSetting': 3.14,
            'stringSetting': 'test'
        }

        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalDictionaryDataSource(source=dictionary,
                                                                          override_behaviour=OverrideBehaviour.LocalOnly))

        self.assertTrue(client.get_value('enabledFeature', False))
        self.assertFalse(client.get_value('disabledFeature', True))
        self.assertEqual(5, client.get_value('intSetting', 0))
        self.assertEqual(3.14, client.get_value('doubleSetting', 0.0))
        self.assertEqual('test', client.get_value('stringSetting', ''))

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_local_over_remote(self, mock_get):
        dictionary = {
            'fakeKey': True,
            'nonexisting': True
        }

        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalDictionaryDataSource(source=dictionary,
                                                                          override_behaviour=OverrideBehaviour.LocalOverRemote))
        client.force_refresh()

        self.assertTrue(client.get_value('fakeKey', False))
        self.assertTrue(client.get_value('nonexisting', False))

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_remote_over_local(self, mock_get):
        dictionary = {
            'fakeKey': True,
            'nonexisting': True
        }

        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalDictionaryDataSource(source=dictionary,
                                                                          override_behaviour=OverrideBehaviour.RemoteOverLocal))
        client.force_refresh()

        self.assertFalse(client.get_value('fakeKey', True))
        self.assertTrue(client.get_value('nonexisting', False))


if __name__ == '__main__':
    unittest.main()
