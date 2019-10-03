import logging
import unittest
import time

import configcatclient
from configcatclient import ConfigCatClientException
from configcatclient.interfaces import LogLevel

logging.basicConfig()

_API_KEY = 'PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA'


class DefaultTests(unittest.TestCase):

    def test_without_api_key(self):
        try:
            configcatclient.create_client(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client(_API_KEY)
        client.set_log_level(LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_get_all_keys(self):
        client = configcatclient.create_client(_API_KEY)
        client.set_log_level(LogLevel.INFO)
        keys = client.get_all_keys()
        self.assertEqual(5, len(keys))
        self.assertTrue('keySampleText' in keys)

    def test_force_refresh(self):
        client = configcatclient.create_client(_API_KEY)
        client.set_log_level(LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()


class AutoPollTests(unittest.TestCase):

    def test_without_api_key(self):
        try:
            configcatclient.create_client_with_auto_poll(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client_with_auto_poll(_API_KEY, log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_auto_poll(_API_KEY, base_url='https://cdn.configcat.com',
                                                              log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url_trailing_slash(self):
        client = configcatclient.create_client_with_auto_poll(_API_KEY, base_url='https://cdn.configcat.com/',
                                                              log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_auto_poll(_API_KEY, base_url='https://invalidcdn.configcat.com',
                                                              log_level=LogLevel.INFO)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_force_refresh(self):
        client = configcatclient.create_client_with_auto_poll(_API_KEY, log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_wrong_param(self):
        client = configcatclient.create_client_with_auto_poll(_API_KEY, 0, -1, log_level=LogLevel.INFO)
        time.sleep(2)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()


class LazyLoadingTests(unittest.TestCase):

    def test_without_api_key(self):
        try:
            configcatclient.create_client_with_lazy_load(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client_with_lazy_load(_API_KEY, log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_lazy_load(_API_KEY, base_url='https://cdn.configcat.com',
                                                              log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_lazy_load(_API_KEY, base_url='https://invalidcdn.configcat.com',
                                                              log_level=LogLevel.INFO)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_wrong_param(self):
        client = configcatclient.create_client_with_lazy_load(_API_KEY, 0, log_level=LogLevel.INFO)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()


class ManualPollingTests(unittest.TestCase):

    def test_without_api_key(self):
        try:
            configcatclient.create_client_with_manual_poll(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client_with_manual_poll(_API_KEY, log_level=LogLevel.INFO)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_manual_poll(_API_KEY, base_url='https://cdn.configcat.com',
                                                                log_level=LogLevel.INFO)
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_manual_poll(_API_KEY, base_url='https://invalidcdn.configcat.com',
                                                                log_level=LogLevel.INFO)
        client.force_refresh()
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()


if __name__ == '__main__':
    unittest.main()
