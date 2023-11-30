import logging
import unittest
import time

from requests.auth import HTTPProxyAuth
from requests import Timeout

import configcatclient
from configcatclient import ConfigCatClientException, ConfigCatOptions, PollingMode

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
            configcatclient.get(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.get(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_get_all_keys(self):
        client = configcatclient.get(_SDK_KEY)
        keys = client.get_all_keys()
        self.assertEqual(5, len(keys))
        self.assertTrue('keySampleText' in keys)
        client.close()

    def test_get_all_values(self):
        client = configcatclient.get(_SDK_KEY)
        all_values = client.get_all_values()
        self.assertEqual(5, len(all_values))
        self.assertEqual('This text came from ConfigCat', all_values['keySampleText'])
        client.close()

    def test_force_refresh(self):
        client = configcatclient.get(_SDK_KEY)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()


class AutoPollTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.get(None, ConfigCatOptions(polling_mode=PollingMode.auto_poll()))
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll()))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_valid_base_url(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll(),
                                                                base_url='https://cdn.configcat.com'))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_valid_base_url_trailing_slash(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll(),
                                                                base_url='https://cdn.configcat.com'))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll(),
                                                                base_url='https://invalidcdn.configcat.com'))
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_proxy(self):
        proxies = {'https': '0.0.0.0:0'}
        proxy_auth = HTTPProxyAuth("test", "test")
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll(),
                                                                proxies=proxies, proxy_auth=proxy_auth))
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    @mock.patch('requests.get', side_effect=Timeout())
    def test_client_works_request_timeout(self, mock_get):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll()))
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_force_refresh(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.auto_poll()))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_wrong_param(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(
            polling_mode=PollingMode.auto_poll(poll_interval_seconds=0, max_init_wait_time_seconds=-1)))
        time.sleep(2)
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()


class LazyLoadingTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.get(None, ConfigCatOptions(polling_mode=PollingMode.lazy_load()))
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.lazy_load()))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_valid_base_url(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.lazy_load(),
                                                                base_url='https://cdn.configcat.com'))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.lazy_load(),
                                                                base_url='https://invalidcdn.configcat.com'))
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_wrong_param(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.lazy_load(0)))
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()


class ManualPollingTests(unittest.TestCase):

    def test_without_sdk_key(self):
        try:
            configcatclient.get(None, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_valid_base_url(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                base_url='https://cdn.configcat.com'))
        client.force_refresh()
        self.assertEqual('This text came from ConfigCat', client.get_value('keySampleText', 'default value'))
        client.close()

    def test_client_works_invalid_base_url(self):
        client = configcatclient.get(_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                base_url='https://invalidcdn.configcat.com'))
        client.force_refresh()
        self.assertEqual('default value', client.get_value('keySampleText', 'default value'))
        client.close()


if __name__ == '__main__':
    unittest.main()
