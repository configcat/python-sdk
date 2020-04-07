import logging
import unittest
import time

from requests.auth import HTTPProxyAuth

import configcatclient
from configcatclient import ConfigCatClientException

logging.basicConfig(level=logging.INFO)

_SDK_KEY = 'PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA'


class DefaultTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.create_client(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_get_all_keys(self):
        client = configcatclient.create_client(_SDK_KEY)
        keys = client.get_all_keys()
        self.assertEqual(5, len(keys))
        self.assertTrue('keySampleText' in keys)

    def test_force_refresh(self):
        client = configcatclient.create_client(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()


class AutoPollTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.create_client_with_auto_poll(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, base_url='https://cdn.configcat.com')
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url_trailing_slash(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, base_url='https://cdn.configcat.com/')
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, base_url='https://invalidcdn.configcat.com')
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_proxy(self):
        proxies = {'https': '0.0.0.0:0'}
        proxy_auth = HTTPProxyAuth("test", "test")
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, proxies=proxies, proxy_auth=proxy_auth)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_force_refresh(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_wrong_param(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, 0, -1)
        time.sleep(2)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()


class LazyLoadingTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.create_client_with_lazy_load(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY, base_url='https://cdn.configcat.com')
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY, base_url='https://invalidcdn.configcat.com')
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_wrong_param(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY, 0)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()


class ManualPollingTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.create_client_with_manual_poll(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.create_client_with_manual_poll(_SDK_KEY)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_manual_poll(_SDK_KEY, base_url='https://cdn.configcat.com')
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.stop()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_manual_poll(_SDK_KEY, base_url='https://invalidcdn.configcat.com')
        client.force_refresh()
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.stop()


if __name__ == '__main__':
    unittest.main()
