# -*- coding: utf-8 -*-
import logging
import unittest

import configcatclient
from configcatclient.user import User

logging.basicConfig(level=logging.INFO)

_SDK_KEY = 'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/u28_1qNyZ0Wz-ldYHIU7-g'


class SpecialCharacterTests(unittest.TestCase):
    def setUp(self):
        self.client = configcatclient.get(_SDK_KEY)

    def tearDown(self):
        self.client.close()

    def test_special_characters_works_cleartext(self):
        actual = self.client.get_value("specialCharacters", "NOT_CAT", User('äöüÄÖÜçéèñışğâ¢™✓😀'))
        self.assertEqual(actual, 'äöüÄÖÜçéèñışğâ¢™✓😀')

    def test_special_characters_works_hashed(self):
        actual = self.client.get_value("specialCharactersHashed", "NOT_CAT", User('äöüÄÖÜçéèñışğâ¢™✓😀'))
        self.assertEqual(actual, 'äöüÄÖÜçéèñışğâ¢™✓😀')


if __name__ == '__main__':
    unittest.main()
