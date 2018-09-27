import unittest
import time

import configcatclient
from configcatclient import ConfigCatClientException


class AutoPollTests(unittest.TestCase):

    def test_get_without_initialization(self):
        configcatclient.stop()
        try:
            configcatclient.get_value('test', 'default')
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_without_api_key(self):
        configcatclient.stop()
        try:
            configcatclient.initialize(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_client_works(self):
        configcatclient.stop()
        configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_force_refresh(self):
        configcatclient.stop()
        configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.force_refresh()
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_reinitialization(self):
        configcatclient.stop()
        configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.initialize('hijack')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_wrong_param(self):
        configcatclient.stop()
        configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA', 0, -1)
        time.sleep(2)
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()


class LazyLoadingTests(unittest.TestCase):

    def test_without_api_key(self):
        configcatclient.stop()
        try:
            configcatclient.initialize_lazy_loading(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_reinitialization(self):
        configcatclient.stop()
        configcatclient.initialize_lazy_loading('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.initialize_lazy_loading('hijack')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_client_works(self):
        configcatclient.stop()
        configcatclient.initialize_lazy_loading('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_wrong_param(self):
        configcatclient.stop()
        configcatclient.initialize_lazy_loading('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA', 0)
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()


class ManualPollingTests(unittest.TestCase):

    def test_without_api_key(self):
        configcatclient.stop()
        try:
            configcatclient.initialize_manual_polling(None)
            self.fail('Expected ConfigCatClientException')
        except ConfigCatClientException:
            pass

    def test_reinitialization(self):
        configcatclient.stop()
        configcatclient.initialize_manual_polling('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        configcatclient.force_refresh()
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.initialize_manual_polling('hijack')
        configcatclient.force_refresh()
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()

    def test_client_works(self):
        configcatclient.stop()
        configcatclient.initialize_manual_polling('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')
        self.assertEqual('default value', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.force_refresh()
        self.assertEqual('This text came from ConfigCat', configcatclient.get_value('keySampleText', 'default value'))
        configcatclient.stop()


if __name__ == '__main__':
    unittest.main()
