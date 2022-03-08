import logging
import unittest

from configcatclient import ConfigCatClient
from configcatclient.localdictionarydatasource import LocalDictionaryDataSource
from configcatclient.overridedatasource import OverrideBehaviour

logging.basicConfig()


class LocalTests(unittest.TestCase):
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

    def test_local_over_remote(self):
        pass

    def test_remote_over_local(self):
        pass


if __name__ == '__main__':
    unittest.main()
