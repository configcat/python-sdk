import logging
import unittest

from configcatclient import DataGovernance
from configcatclient.configcatoptions import Hooks
from configcatclient.logger import Logger
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

from configcatclient.configfetcher import ConfigFetcher

logging.basicConfig(level=logging.WARN)
log = Logger('configcat', Hooks())

FEATURE_TEST_JSON = {"test": "json"}


# An organization with Global data_governance config.json representation
def mocked_requests_get_global(*args, **kwargs):
    if args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 0
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    elif args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 0
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    return MockResponse(None, 404)


# An organization with EuOnly data_governance config.json representation
def mocked_requests_get_eu_only(*args, **kwargs):
    if args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-eu.configcat.com",
                "r": 1
            },
            "f": {}
        }, 200)
    elif args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-eu.configcat.com",
                "r": 0
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    return MockResponse(None, 404)


# An organization with Global data_governance config.json representation with custom baseurl
def mocked_requests_get_custom(*args, **kwargs):
    if args[0] == 'https://custom.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 0
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    return MockResponse(None, 404)


# Redirect loop in config.json
def mocked_requests_get_redirect_loop(*args, **kwargs):
    if args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-eu.configcat.com",
                "r": 1
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    elif args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://cdn-global.configcat.com",
                "r": 1
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    return MockResponse(None, 404)


# An organization with forced=2 redirection config.json representation
def mocked_requests_get_forced_2(*args, **kwargs):
    if args[0] == 'https://custom.configcat.com/configuration-files//config_v6.json' \
            or args[0] == 'https://cdn-global.configcat.com/configuration-files//config_v6.json' \
            or args[0] == 'https://cdn-eu.configcat.com/configuration-files//config_v6.json'\
            or args[0] == 'https://forced.configcat.com/configuration-files//config_v6.json':
        return MockResponse({
            "p": {
                "u": "https://forced.configcat.com",
                "r": 2
            },
            "f": FEATURE_TEST_JSON
        }, 200)
    return MockResponse(None, 404)


call_to_global = mock.call('https://cdn-global.configcat.com/configuration-files//config_v6.json',
                           auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)
call_to_eu = mock.call('https://cdn-eu.configcat.com/configuration-files//config_v6.json',
                       auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)
call_to_custom = mock.call('https://custom.configcat.com/configuration-files//config_v6.json',
                           auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)
call_to_forced = mock.call('https://forced.configcat.com/configuration-files//config_v6.json',
                           auth=ANY, headers=ANY, proxies=ANY, timeout=ANY)


class DataGovernanceTests(unittest.TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get_global)
    def test_sdk_global_organization_global(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-global.configcat.com
        # and the second should call https://cdn-global.configcat.com
        # without force redirects

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
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
        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.EuOnly)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_global, mock_get.call_args_list[1])

    @mock.patch('requests.get', side_effect=mocked_requests_get_eu_only)
    def test_sdk_global_organization_eu_only(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-global.configcat.com
        # with an immediate redirect to https://cdn-eu.configcat.com
        # and the second should call https://cdn-eu.configcat.com

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
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

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.EuOnly)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])

    @mock.patch('requests.get', side_effect=mocked_requests_get_custom)
    def test_sdk_global_custom_base_url(self, mock_get):
        # In this case
        # the first invocation should call https://custom.configcat.com
        # and the second should call https://custom.configcat.com
        # without force redirects

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.Global,
                                base_url='https://custom.configcat.com')

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
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

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.EuOnly,
                                base_url='https://custom.configcat.com')

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 1)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_custom, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_forced_2)
    def test_sdk_global_forced(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-global.configcat.com
        # with an immediate redirect to https://forced.configcat.com
        # and the second should call https://forced.configcat.com

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
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

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.EuOnly)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_eu, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
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
                                log=log,
                                base_url='https://custom.configcat.com')

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 2)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 3)
        self.assertEqual(call_to_custom, mock_get.call_args_list[0])
        self.assertEqual(call_to_forced, mock_get.call_args_list[1])
        self.assertEqual(call_to_forced, mock_get.call_args_list[2])
        self.assertNotIn(call_to_eu, mock_get.call_args_list)
        self.assertNotIn(call_to_global, mock_get.call_args_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get_redirect_loop)
    def test_sdk_redirect_loop(self, mock_get):
        # In this case
        # the first invocation should call https://cdn-global.configcat.com
        # with an immediate redirect to https://cdn-eu.configcat.com
        # with an immediate redirect to https://cdn-global.configcat.com
        # the second invocation should call https://cdn-eu.configcat.com
        # with an immediate redirect to https://cdn-global.configcat.com
        # with an immediate redirect to https://cdn-eu.configcat.com

        fetcher = ConfigFetcher(sdk_key='', log=log, mode='m', data_governance=DataGovernance.Global)

        # First fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 3)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])
        self.assertEqual(call_to_global, mock_get.call_args_list[2])

        # Second fetch
        fetch_response = fetcher.get_configuration()
        config = fetch_response.entry.config
        self.assertTrue(fetch_response.is_fetched())
        self.assertEqual(FEATURE_TEST_JSON, config.get('f'))
        self.assertEqual(len(mock_get.call_args_list), 6)
        self.assertEqual(call_to_global, mock_get.call_args_list[0])
        self.assertEqual(call_to_eu, mock_get.call_args_list[1])
        self.assertEqual(call_to_global, mock_get.call_args_list[2])
        self.assertEqual(call_to_eu, mock_get.call_args_list[3])
        self.assertEqual(call_to_global, mock_get.call_args_list[4])
        self.assertEqual(call_to_eu, mock_get.call_args_list[5])
