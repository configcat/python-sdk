import unittest
import json
from datetime import datetime

from configcatclient.user import User


class UserTests(unittest.TestCase):
    def test_empty_or_none_identifier(self):
        u1 = User(None)
        self.assertEqual('', u1.get_identifier())
        u2 = User('')
        self.assertEqual('', u2.get_identifier())

    def test_attribute_case_sensitivity(self):
        user_id = 'id'
        email = 'test@test.com'
        country = 'country'
        custom = {'custom': 'test'}
        user = User(identifier=user_id, email=email, country=country, custom=custom)

        self.assertEqual(user_id, user.get_identifier())

        self.assertEqual(email, user.get_attribute('Email'))
        self.assertIsNone(user.get_attribute('EMAIL'))
        self.assertIsNone(user.get_attribute('email'))

        self.assertEqual(country, user.get_attribute('Country'))
        self.assertIsNone(user.get_attribute('COUNTRY'))
        self.assertIsNone(user.get_attribute('country'))

        self.assertEqual('test', user.get_attribute('custom'))
        self.assertIsNone(user.get_attribute('non-existing'))

    def test_to_str(self):
        user_id = 'id'
        email = 'test@test.com'
        country = 'country'
        custom = {'custom': 'test'}
        user = User(identifier=user_id, email=email, country=country, custom=custom)

        user_json = json.loads(str(user))

        self.assertEqual(user_id, user_json['Identifier'])
        self.assertEqual(email, user_json['Email'])
        self.assertEqual(country, user_json['Country'])
        self.assertEqual('test', user_json['custom'])

    def test_attribute_value_from_datetime(self):
        self.assertEqual(User.attribute_value_from_datetime(datetime(2023, 9, 19, 11, 1, 35)), '1695121295.0')
        self.assertEqual(User.attribute_value_from_datetime(datetime(2023, 9, 19, 11, 1, 35, 510886)), '1695121295.510886')

    def test_attribute_value_from_list(self):
        self.assertEqual(User.attribute_value_from_list(['a', 'b', 'c']), '["a", "b", "c"]')
