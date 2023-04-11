import logging
import unittest

from configcatclient.utils import method_is_called_from

logging.basicConfig(level=logging.INFO)


def no_operation():
    pass


def test_method_is_called_from():
    pass


class OtherClass:
    def no_operation(self):
        pass

    def test_method_is_called_from(self):
        pass


class UtilsTests(unittest.TestCase):
    def no_operation(self):
        pass

    def test_method_is_called_from(self):
        class TestClass:
            @classmethod
            def class_method(cls, method):
                return method_is_called_from(method)

            def object_method(self, method):
                return method_is_called_from(method)

        self.assertTrue(TestClass.class_method(UtilsTests.test_method_is_called_from))
        self.assertTrue(TestClass().object_method(UtilsTests.test_method_is_called_from))

        self.assertFalse(TestClass.class_method(UtilsTests.no_operation))
        self.assertFalse(TestClass().object_method(UtilsTests.no_operation))

        self.assertFalse(TestClass.class_method(no_operation))
        self.assertFalse(TestClass().object_method(test_method_is_called_from))
        self.assertFalse(TestClass.class_method(OtherClass.no_operation))
        self.assertFalse(TestClass().object_method(OtherClass.test_method_is_called_from))


if __name__ == '__main__':
    unittest.main()
