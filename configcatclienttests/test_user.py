import unittest
from configcatclient.user import User


class UserTests(unittest.TestCase):
    def test_empty_or_none_identifier(self):
        u1 = User(None)
        self.assertEqual('', u1.get_identifier())
        u2 = User('')
        self.assertEqual('', u2.get_identifier())

    def test_attribute_case_sensitivity(self):
        email = 'test@test.com'
        country = 'country'
        user = User('user_id', email=email, country=country)
        self.assertEqual(email, user.get_attribute("Email"))
        self.assertIsNone(user.get_attribute("EMAIL"))
        self.assertIsNone(user.get_attribute("email"))

        self.assertEqual(country, user.get_attribute("Country"))
        self.assertIsNone(user.get_attribute("COUNTRY"))
        self.assertIsNone(user.get_attribute("country"))
