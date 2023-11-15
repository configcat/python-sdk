import logging
import unittest
import json
from datetime import datetime
from parameterized import parameterized

from configcatclient.configcatoptions import Hooks
from configcatclient.rolloutevaluator import RolloutEvaluator
from configcatclient.user import User
from configcatclient.logger import Logger
from configcatclienttests.mocks import MockLogHandler

logging.basicConfig()


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
        self.assertEqual(User.attribute_value_from_datetime(datetime(2023, 9, 19, 11, 1, 35, 510000)), '1695121295.51')

    def test_attribute_value_from_list(self):
        self.assertEqual(User.attribute_value_from_list(['a', 'b', 'c']), '["a", "b", "c"]')

    @parameterized.expand([
        ('identifierAttribute', False, "False"),
        ('emailAttribute', False, "False"),
        ('countryAttribute', False, "False"),
        ('Custom1', False, "False"),
        ('identifierAttribute', 1.23, "1.23"),
        ('emailAttribute', 1.23, "1.23"),
        ('countryAttribute', 1.23, "1.23"),
        ('Custom1', 1.23, "1.23"),
    ])
    def test_non_string_attribute(self, attribute_name, attribute_value, comparison_value):
        config = {
            'f': {
                'test': {
                    't': 0,
                    'r': [
                        {
                            'c': [
                                {
                                    'u': {'a': attribute_name, 'c': 1, 'l': [comparison_value]}
                                }
                            ],
                            's': {'v': {'b': False}}
                        },
                        {
                            'c': [
                                {
                                    'u': {'a': attribute_name, 'c': 0, 'l': [comparison_value]}
                                }
                            ],
                            's': {'v': {'b': True}}
                        },
                    ],
                    'v': {'b': False}
                }
            }
        }

        user = User(identifier='id', custom={attribute_name: attribute_value})
        log_builder = None
        log = Logger('configcat', Hooks())
        logger = logging.getLogger('configcat')
        log_handler = MockLogHandler()
        logger.addHandler(log_handler)
        evaluator = RolloutEvaluator(log)
        value, _, _, _, _ = evaluator.evaluate('test', user, 'default_value', 'default_variation_id', config, log_builder)

        self.assertTrue(value)
        self.assertEqual(1, len(log_handler.warning_logs))
        self.assertTrue(log_handler.warning_logs[0].startswith('[4004]'))

