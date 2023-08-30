import datetime
import logging
import unittest
import requests

from configcatclient.configcatclient import ConfigCatClient
from configcatclient.constants import FEATURE_FLAGS, VALUE, COMPARATOR, COMPARISON_ATTRIBUTE, SERVED_VALUE, STRING_VALUE
from configcatclient.user import User
from configcatclient.configcatoptions import ConfigCatOptions, Hooks
from configcatclient.pollingmode import PollingMode
from configcatclient.utils import get_utc_now
from configcatclienttests.mocks import ConfigCacheMock, HookCallbacks, TEST_OBJECT, TEST_SDK_KEY

# Python2/Python3 support
try:
    from unittest import mock
except ImportError:
    import mock
try:
    from unittest.mock import Mock, ANY
except ImportError:
    from mock import Mock, ANY

logging.basicConfig(level=logging.INFO)


class HooksTests(unittest.TestCase):

    def test_init(self):
        hook_callbacks = HookCallbacks()
        hooks = Hooks(
            on_client_ready=hook_callbacks.on_client_ready,
            on_config_changed=hook_callbacks.on_config_changed,
            on_flag_evaluated=hook_callbacks.on_flag_evaluated,
            on_error=hook_callbacks.on_error
        )

        config_cache = ConfigCacheMock()
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=config_cache,
                                                                    hooks=hooks))

        value = client.get_value('testStringKey', '')

        self.assertEqual('testValue', value)
        self.assertTrue(hook_callbacks.is_ready)
        self.assertEqual(1, hook_callbacks.is_ready_call_count)
        self.assertEqual(TEST_OBJECT.get(FEATURE_FLAGS), hook_callbacks.changed_config)
        self.assertEqual(1, hook_callbacks.changed_config_call_count)
        self.assertTrue(hook_callbacks.evaluation_details)
        self.assertEqual(1, hook_callbacks.evaluation_details_call_count)
        self.assertIsNone(hook_callbacks.error)
        self.assertEqual(0, hook_callbacks.error_call_count)

        client.close()

    def test_subscribe(self):
        hook_callbacks = HookCallbacks()
        hooks = Hooks()
        hooks.add_on_client_ready(hook_callbacks.on_client_ready)
        hooks.add_on_config_changed(hook_callbacks.on_config_changed)
        hooks.add_on_flag_evaluated(hook_callbacks.on_flag_evaluated)
        hooks.add_on_error(hook_callbacks.on_error)

        config_cache = ConfigCacheMock()
        client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                    config_cache=config_cache,
                                                                    hooks=hooks))

        value = client.get_value('testStringKey', '')

        self.assertEqual('testValue', value)
        self.assertTrue(hook_callbacks.is_ready)
        self.assertEqual(1, hook_callbacks.is_ready_call_count)
        self.assertEqual(TEST_OBJECT.get(FEATURE_FLAGS), hook_callbacks.changed_config)
        self.assertEqual(1, hook_callbacks.changed_config_call_count)
        self.assertTrue(hook_callbacks.evaluation_details)
        self.assertEqual(1, hook_callbacks.evaluation_details_call_count)
        self.assertIsNone(hook_callbacks.error)
        self.assertEqual(0, hook_callbacks.error_call_count)

        client.close()

    def test_evaluation(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            hook_callbacks = HookCallbacks()
            client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll()))

            client.get_hooks().add_on_flag_evaluated(hook_callbacks.on_flag_evaluated)

            client.force_refresh()

            user = User("test@test1.com")
            value = client.get_value('testStringKey', '', user)
            self.assertEqual('fake1', value)

            details = hook_callbacks.evaluation_details
            self.assertEqual('fake1', details.value)
            self.assertEqual('testStringKey', details.key)
            self.assertEqual('id1', details.variation_id)
            self.assertFalse(details.is_default_value)
            self.assertIsNone(details.error)
            self.assertIsNone(details.matched_percentage_rule)
            self.assertEqual('fake1', details.matched_targeting_rule[SERVED_VALUE][VALUE][STRING_VALUE])
            self.assertEqual(str(user), str(details.user))
            now = get_utc_now()
            self.assertGreaterEqual(now, details.fetch_time)
            self.assertLessEqual(now, details.fetch_time + + datetime.timedelta(seconds=1))

            client.close()

    def test_callback_exception(self):
        with mock.patch.object(requests, 'get') as request_get:
            response_mock = Mock()
            request_get.return_value = response_mock
            response_mock.json.return_value = TEST_OBJECT
            response_mock.status_code = 200
            response_mock.headers = {}

            hook_callbacks = HookCallbacks()
            hooks = Hooks(
                on_client_ready=hook_callbacks.callback_exception,
                on_config_changed=hook_callbacks.callback_exception,
                on_flag_evaluated=hook_callbacks.callback_exception,
                on_error=hook_callbacks.callback_exception
            )
            client = ConfigCatClient.get(TEST_SDK_KEY, ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                                        hooks=hooks))

            client.force_refresh()

            value = client.get_value('testStringKey', '')
            self.assertEqual('testValue', value)

            value = client.get_value('', 'default')
            self.assertEqual('default', value)


if __name__ == '__main__':
    unittest.main()
