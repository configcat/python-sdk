import logging
import unittest
import requests

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from configcatclient.configfetcher import ConfigFetcher, FetchResponse

logging.basicConfig(level=logging.WARN)
log = logging.getLogger()


class ConfigFetcherTests(unittest.TestCase):
    def test_simple_fetch_success(self):
        with mock.patch.object(requests, 'get') as request_get:
            test_json = {"test": "json"}
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = test_json
            response_mock.status_code = 200
            response_mock.headers = {}
            fetcher = ConfigFetcher(sdk_key='', log=log, mode='m')
            fetch_response = fetcher.get_configuration_json()
            self.assertTrue(fetch_response.is_fetched())
            self.assertEqual(test_json, fetch_response.json()[FetchResponse.CONFIG])

    def test_fetch_not_modified_etag(self):
        with mock.patch.object(requests, 'get') as request_get:
            etag = 'test'
            test_json = {"test": "json"}
            fetcher = ConfigFetcher(sdk_key='', log=log, mode='m')

            response_mock = Mock()
            response_mock.json.return_value = test_json
            response_mock.status_code = 200
            response_mock.headers = {'Etag': etag}

            request_get.return_value = response_mock
            fetch_response = fetcher.get_configuration_json()
            self.assertTrue(fetch_response.is_fetched())
            self.assertEqual(test_json, fetch_response.json()[FetchResponse.CONFIG])
            self.assertEqual(etag, fetch_response.json()[FetchResponse.ETAG])

            response_not_modified_mock = Mock()
            response_not_modified_mock.json.return_value = {}
            response_not_modified_mock.status_code = 304
            response_not_modified_mock.headers = {'ETag': etag}

            request_get.return_value = response_not_modified_mock
            fetch_response = fetcher.get_configuration_json(etag)
            self.assertFalse(fetch_response.is_fetched())

            args, kwargs = request_get.call_args
            request_headers = kwargs.get('headers')
            self.assertEqual(request_headers.get('If-None-Match'), etag)

    def test_server_side_etag(self):
        fetcher = ConfigFetcher(sdk_key='PKDVCLf-Hq-h-kCzMp-L7Q/HhOWfwVtZ0mb30i9wi17GQ',
                                log=log,
                                mode='m', base_url='https://cdn-eu.configcat.com')
        fetch_response = fetcher.get_configuration_json()
        etag = fetch_response.json()[FetchResponse.ETAG]
        self.assertIsNotNone(etag)
        self.assertNotEqual('', etag)
        self.assertTrue(fetch_response.is_fetched())
        self.assertFalse(fetch_response.is_not_modified())

        fetch_response = fetcher.get_configuration_json(etag)
        self.assertFalse(fetch_response.is_fetched())
        self.assertTrue(fetch_response.is_not_modified())

        fetch_response = fetcher.get_configuration_json('')
        self.assertTrue(fetch_response.is_fetched())
        self.assertFalse(fetch_response.is_not_modified())
