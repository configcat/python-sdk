import unittest
import time

import configcatclient
from configcatclient import ConfigCatClientException


class AutoPollTests(unittest.TestCase):

    def test_get_without_initialization(self):
        configcatclient.stop()
        with self.assertRaises(ConfigCatClientException):
            configcatclient.get()

    def test_without_project_secret(self):
        configcatclient.stop()
        with self.assertRaises(ConfigCatClientException):
            configcatclient.initialize(None)

    def test_client_works(self):
        configcatclient.stop()
        configcatclient.initialize('samples/01')
        client = configcatclient.get()
        self.assertEqual('This text came from BetterConfig', client.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_get_configuration(self):
        configcatclient.stop()
        configcatclient.initialize('samples/01')
        client = configcatclient.get()
        configuration_json = client.get_configuration_json()
        self.assertEqual('This text came from BetterConfig', configuration_json['keySampleText'])
        configcatclient.stop()

    def test_force_refresh(self):
        configcatclient.stop()
        configcatclient.initialize('samples/01')
        client = configcatclient.get()
        configuration_json = client.get_configuration_json()
        self.assertEqual('This text came from BetterConfig', configuration_json['keySampleText'])
        client.force_refresh()
        configuration_json = client.get_configuration_json()
        self.assertEqual('This text came from BetterConfig', configuration_json['keySampleText'])
        configcatclient.stop()

    def test_reinitialization(self):
        configcatclient.stop()
        configcatclient.initialize('samples/01')
        self.assertEqual(configcatclient.get()._project_secret, 'samples/01')
        configcatclient.initialize('hijack')
        self.assertEqual(configcatclient.get()._project_secret, 'samples/01')
        configcatclient.stop()

    def test_wrong_param(self):
        configcatclient.stop()
        configcatclient.initialize('samples/01', 0, -1)
        client = configcatclient.get()
        time.sleep(1)
        self.assertEqual('This text came from BetterConfig', client.get_value('keySampleText', 'default value'))
        configcatclient.stop()


class LazyLoadingTests(unittest.TestCase):

    def test_without_project_secret(self):
        configcatclient.stop()
        with self.assertRaises(ConfigCatClientException):
            configcatclient.initialize_lazy_loading(None)

    def test_reinitialization(self):
        configcatclient.stop()
        configcatclient.initialize_lazy_loading('samples/01')
        self.assertEqual(configcatclient.get()._project_secret, 'samples/01')
        configcatclient.initialize_lazy_loading('hijack')
        self.assertEqual(configcatclient.get()._project_secret, 'samples/01')
        configcatclient.stop()

    def test_client_works(self):
        configcatclient.stop()
        configcatclient.initialize_lazy_loading('samples/01')
        client = configcatclient.get()
        self.assertEqual('This text came from BetterConfig', client.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_wrong_param(self):
        configcatclient.stop()
        configcatclient.initialize_lazy_loading('samples/01', 0)
        client = configcatclient.get()
        self.assertEqual('This text came from BetterConfig', client.get_value('keySampleText', 'default value'))
        configcatclient.stop()


class ManualPollingTests(unittest.TestCase):

    def test_without_project_secret(self):
        configcatclient.stop()
        with self.assertRaises(ConfigCatClientException):
            configcatclient.initialize_manual_polling(None)

    def test_reinitialization(self):
        configcatclient.stop()
        configcatclient.initialize_manual_polling('samples/01')
        self.assertEqual(configcatclient.get()._project_secret, 'samples/01')
        configcatclient.initialize_manual_polling('hijack')
        self.assertEqual(configcatclient.get()._project_secret, 'samples/01')
        configcatclient.stop()

    def test_client_works(self):
        configcatclient.stop()
        configcatclient.initialize_manual_polling('samples/01')
        client = configcatclient.get()
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from BetterConfig', client.get_value('keySampleText', 'default value'))
        configcatclient.stop()


if __name__ == '__main__':
    unittest.main()
