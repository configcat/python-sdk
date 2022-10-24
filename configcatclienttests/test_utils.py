import logging
import unittest

from configcatclient.utils import method_is_called_from

logging.basicConfig(level=logging.INFO)


class UtilsTests(unittest.TestCase):
    def no_operation(self):
        pass

    def test_method_is_called_from(self):
        class TestClass(object):
            @classmethod
            def class_method(cls, method):
                return method_is_called_from(method)

            def object_method(self, method):
                return method_is_called_from(method)

        self.assertTrue(TestClass.class_method(UtilsTests.test_method_is_called_from))
        self.assertTrue(TestClass().object_method(UtilsTests.test_method_is_called_from))
        self.assertFalse(TestClass.class_method(UtilsTests.no_operation))
        self.assertFalse(TestClass().object_method(UtilsTests.no_operation))


if __name__ == '__main__':
    unittest.main()
