import logging
import unittest
import time

from requests.auth import HTTPProxyAuth
from requests import Timeout

import configcatclient
from configcatclient import ConfigCatClientException

logging.basicConfig(level=logging.INFO)

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

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
        client.close()

    def test_get_all_keys(self):
        client = configcatclient.create_client(_SDK_KEY)
        keys = client.get_all_keys()
        self.assertEqual(5, len(keys))
        self.assertTrue('keySampleText' in keys)

    def test_get_all_values(self):
        client = configcatclient.create_client(_SDK_KEY)
        all_values = client.get_all_values()
        self.assertEqual(5, len(all_values))
        self.assertEqual('This text came from ConfigCat', all_values['keySampleText'])

    def test_force_refresh(self):
        client = configcatclient.create_client(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()


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
        client.close()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, base_url='https://cdn.configcat.com')
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_valid_base_url_trailing_slash(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, base_url='https://cdn.configcat.com/')
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, base_url='https://invalidcdn.configcat.com')
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_proxy(self):
        proxies = {'https': '0.0.0.0:0'}
        proxy_auth = HTTPProxyAuth("test", "test")
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY, proxies=proxies, proxy_auth=proxy_auth)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    @mock.patch('requests.get', side_effect=Timeout())
    def test_client_works_request_timeout(self, mock_get):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY)
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_force_refresh(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_wrong_param(self):
        client = configcatclient.create_client_with_auto_poll(_SDK_KEY,
                                                              poll_interval_seconds=0,
                                                              max_init_wait_time_seconds=-1)
        time.sleep(2)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()


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
        client.close()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY, base_url='https://cdn.configcat.com')
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY, base_url='https://invalidcdn.configcat.com')
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_wrong_param(self):
        client = configcatclient.create_client_with_lazy_load(_SDK_KEY, 0)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()


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
        client.close()

    def test_client_works_valid_base_url(self):
        client = configcatclient.create_client_with_manual_poll(_SDK_KEY, base_url='https://cdn.configcat.com')
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.create_client_with_manual_poll(_SDK_KEY, base_url='https://invalidcdn.configcat.com')
        client.force_refresh()
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()


if __name__ == '__main__':
    unittest.main()
