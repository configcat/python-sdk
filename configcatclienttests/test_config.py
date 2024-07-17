import logging
import unittest

import pytest

from configcatclient.config import get_value, SETTING_TYPE

logging.basicConfig(level=logging.INFO)


class ConfigTests(unittest.TestCase):
    def test_value_setting_type_is_missing(self):
        value_dictionary = {
            't': 6,  # unsupported setting type
            'v': {
                'b': True
            }
        }
        setting_type = value_dictionary.get(SETTING_TYPE)
        with pytest.raises(ValueError) as e:
            get_value(value_dictionary, setting_type)
        assert str(e.value) == "Unsupported setting type"

    def test_value_setting_type_is_valid_but_return_value_is_missing(self):
        value_dictionary = {
            't': 0,  # boolean
            'v': {
                's': True  # the wrong property is set ("b" should be set)
            }
        }
        setting_type = value_dictionary.get(SETTING_TYPE)
        with pytest.raises(ValueError) as e:
            get_value(value_dictionary, setting_type)
        assert str(e.value) == "Setting value is not of the expected type <class 'bool'>"

    def test_value_setting_type_is_valid_and_the_return_value_is_present_but_it_is_invalid(self):
        value_dictionary = {
            't': 0,  # boolean
            'v': {
                'b': 'True'  # the value is a string instead of a boolean
            }
        }
        setting_type = value_dictionary.get(SETTING_TYPE)
        with pytest.raises(ValueError) as e:
            get_value(value_dictionary, setting_type)
        assert str(e.value) == "Setting value is not of the expected type <class 'bool'>"


if __name__ == '__main__':
    unittest.main()
