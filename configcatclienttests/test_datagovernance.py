import logging
import unittest
import requests

from configcatclient import DataGovernance

try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

from configcatclient.configfetcher import ConfigFetcher

logging.basicConfig(level=logging.WARN)

test_json = {"test": "json"}


class MockHeader:
    def __init__(self, etag):
        self.etag = etag

    def get(self, name):
        if name == 'Etag':
            return self.etag
        return None


class MockResponse:
    def __init__(self, json_data, status_code, etag=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = MockHeader(etag)

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if 200 <= self.status_code < 300 or self.status_code == 304:
            return
        raise Exception(self.status_code)


# An organization with Global data_governance config.json representation
def mocked_requests_get_global(*args, **kwargs):
    if args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v5.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 0
            },
            "f": test_json
        }, 200)
    elif args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v5.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 0
            },
            "f": test_json
        }, 200)
    return MockResponse(None, 404)


# An organization with EuOnly data_governance config.json representation
def mocked_requests_get_eu_only(*args, **kwargs):
    if args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v5.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-eu.configcat.com",
                "r": 1
            },
            "f": {}
        }, 200)
    elif args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v5.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-eu.configcat.com",
                "r": 0
            },
            "f": test_json
        }, 200)
    return MockResponse(None, 404)


# An organization with Global data_governance config.json representation with custom baseurl
def mocked_requests_get_custom(*args, **kwargs):
    if args[0] == 'https://custom.configcat.com/configuration-files//config_v5.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 0
            },
            "f": test_json
        }, 200)
    return MockResponse(None, 404)


# An organization with forced=2 redirection config.json representation
def mocked_requests_get_forced_2(*args, **kwargs):
    if args[0] == 'https://custom.configcat.com/configuration-files//config_v5.json' \
            or args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v5.json' \
            or args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v5.json'\
            or args[0] == 'https://forced.configcat.com/configuration-files//config_v5.json':
        return MockResponse({
            "p": {
                "u": "https://forced.configcat.com",
                "r": 2
            },
            "f": test_json
        }, 200)
    return MockResponse(None, 404)


call_to_global = mock.call('https://cdn-global.configcat.com/configuration-files//config_v5.json',
                           auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)
call_to_eu = mock.call('https://cdn-eu.configcat.com/configuration-files//config_v5.json',
                       auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)
call_to_custom = mock.call('https://custom.configcat.com/configuration-files//config_v5.json',
                           auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)
call_to_forced = mock.call('https://forced.configcat.com/configuration-files//config_v5.json',
                           auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)


class DataGovernanceTests(unittest.TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get_global)
    def test_sdk_global_organization_global(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-global.configcat.com
        # and the second should call https://cdn-global.configcat.com
        # without force redirects

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_global, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_global)
    def test_sdk_eu_organization_global(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-eu.configcat.com
        # and the second should call https://cdn-global.configcat.com
        # without force redirects
        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.EuOnly)

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_global, mock_get.call_args_list[1])

    @mock.patch('requests.get', side_effect=mocked_requests_get_eu_only)
    def test_sdk_global_organization_eu_only(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-global.configcat.com
        # with an immediate redirect to https://cdn-eu.configcat.com
        # and the second should call https://cdn-eu.configcat.com

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 3)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])
        self.assertEqual(call_to_eu, mock_get.call_args_list[2])

    @mock.patch('requests.get', side_effect=mocked_requests_get_eu_only)
    def test_sdk_eu_organization_eu_only(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-eu.configcat.com
        # and the second should call https://cdn-eu.configcat.com
        # without redirects

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.EuOnly)

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])

    @mock.patch('requests.get', side_effect=mocked_requests_get_custom)
    def test_sdk_global_custom_base_url(self, mock_get):
        # In this case
        # the first invocation should call https://custom.configcat.com
        # and the second should call https://custom.configcat.com
        # without force redirects

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.Global,
                                base_url='https://custom.configcat.com')

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_custom, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_custom)
    def test_sdk_eu_custom_base_url(self, mock_get):
        # In this case
        # the first invocation should call https://custom.configcat.com
        # and the second should call https://custom.configcat.com
        # without force redirects

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.EuOnly,
                                base_url='https://custom.configcat.com')

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_custom, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_forced_2)
    def test_sdk_global_forced(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-eu.configcat.com
        # with an immediate redirect to https://forced.configcat.com
        # and the second should call https://forced.configcat.com

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 3)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertEqual(call_to_forced, mock_get.call_args_list[2])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_forced_2)
    def test_sdk_eu_forced(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-eu.configcat.com
        # with an immediate redirect to https://forced.configcat.com
        # and the second should call https://forced.configcat.com

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.EuOnly)

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 3)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertEqual(call_to_forced, mock_get.call_args_list[2])
        self.assertNotIn(call_to_global, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_forced_2)
    def test_sdk_base_url_forced(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-eu.configcat.com
        # with an immediate redirect to https://forced.configcat.com
        # and the second should call https://forced.configcat.com

        fetcher = ConfigFetcher(sdk_key='', mode='m', data_governance=DataGovernance.Global,
                                base_url='https://custom.configcat.com')

        # First fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration_json()
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(test_json, fetch_response.json().get('f'))
        self.assertEqual(len(mock_get.call_args_list), 3)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertEqual(call_to_forced, mock_get.call_args_list[2])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)
