import logging
import unittest

from configcatclient import ConfigCatClientException
from configcatclient.configcatclient import ConfigCatClient
from configcatclient.user import User
from configcatclient.configcatoptions import ConfigCatOptions, Hooks
from configcatclient.pollingmode import PollingMode
from configcatclienttests.mocks import ConfigCacheMock, HookCallbacks

logging.basicConfig(level=logging.INFO)


class HooksTests(unittest.TestCase):
    def test_hooks_init(self):
        hook_callbacks = HookCallbacks()
        hooks = Hooks()
        hooks.add_on_ready(hook_callbacks.on_ready)
        hooks.add_on_config_changed(hook_callbacks.on_config_changed)
        hooks.add_on_flag_evaluated(hook_callbacks.on_flag_evaluated)
        hooks.add_on_error(hook_callbacks.on_error)

        client = ConfigCatClient.get('test', ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                                              config_cache=ConfigCacheMock(),
                                                              hooks=hooks))

        value = client.get_value('testStringKey', '')

        self.assertEqual('testValue', value)
        self.assertTrue(hook_callbacks.is_ready)
        self.assertTrue(hook_callbacks.changed_config)
        self.assertTrue(hook_callbacks.evaluation_details)
        self.assertIsNone(hook_callbacks.error)

        client.close()


if __name__ == '__main__':
    unittest.main()
