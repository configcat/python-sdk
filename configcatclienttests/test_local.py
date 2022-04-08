import logging
import unittest
from os import path
import tempfile
import json
import shutil

from configcatclient import ConfigCatClient
from configcatclient.localdictionarydatasource import LocalDictionaryDataSource
from configcatclient.localfiledatasource import LocalFileDataSource
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
    script_dir = path.dirname(__file__)

    def test_file(self):
        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalFileDataSource(file_path=path.join(LocalTests.script_dir, 'test.json'),
                                                                    override_behaviour=OverrideBehaviour.LocalOnly))

        self.assertTrue(client.get_value('enabledFeature', False))
        self.assertFalse(client.get_value('disabledFeature', True))
        self.assertEqual(5, client.get_value('intSetting', 0))
        self.assertEqual(3.14, client.get_value('doubleSetting', 0.0))
        self.assertEqual('test', client.get_value('stringSetting', ''))
        client.stop()

    def test_simple_file(self):
        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalFileDataSource(file_path=path.join(LocalTests.script_dir, 'test-simple.json'),
                                                                    override_behaviour=OverrideBehaviour.LocalOnly))

        self.assertTrue(client.get_value('enabledFeature', False))
        self.assertFalse(client.get_value('disabledFeature', True))
        self.assertEqual(5, client.get_value('intSetting', 0))
        self.assertEqual(3.14, client.get_value('doubleSetting', 0.0))
        self.assertEqual('test', client.get_value('stringSetting', ''))
        client.stop()

    def test_non_existent_file(self):
        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalFileDataSource(file_path='non_existent.json',
                                                                    override_behaviour=OverrideBehaviour.LocalOnly))
        self.assertFalse(client.get_value('enabledFeature', False))
        client.stop()

    def test_reload_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            temp_path = path.join(temp_dir, 'test-simple.json')
            dictionary = {'flags': {
                'enabledFeature': False
            }}
            with open(temp_path, 'w') as f:
                json.dump(dictionary, f)

            client = ConfigCatClient(sdk_key='test',
                                     poll_interval_seconds=0,
                                     max_init_wait_time_seconds=0,
                                     flag_overrides=LocalFileDataSource(file_path=temp_path,
                                                                        override_behaviour=OverrideBehaviour.LocalOnly))

            self.assertFalse(client.get_value('enabledFeature', True))

            # test
            with open(temp_path, 'r') as f:
                print(f.read())

            import time
            time.sleep(2)
            # test

            # change the temporary file
            dictionary['flags']['enabledFeature'] = True
            with open(temp_path, 'w') as f:
                json.dump(dictionary, f)

            # test
            with open(temp_path, 'r') as f:
                print(f.read())
            # test

            self.assertTrue(client.get_value('enabledFeature', False))

            client.stop()
        finally:
            shutil.rmtree(temp_dir)

    def test_invalid_file(self):
        temp = tempfile.NamedTemporaryFile(mode="w")
        temp.write('{"flags": {"enabledFeature": true}')
        temp.flush()

        client = ConfigCatClient(sdk_key='test',
                                 poll_interval_seconds=0,
                                 max_init_wait_time_seconds=0,
                                 flag_overrides=LocalFileDataSource(file_path=temp.name,
                                                                    override_behaviour=OverrideBehaviour.LocalOnly))

        self.assertFalse(client.get_value('enabledFeature', False))

        client.stop()

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
        client.stop()

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
        client.stop()

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
        client.stop()


if __name__ == '__main__':
    unittest.main()
