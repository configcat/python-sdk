import logging
import sys
import unittest
from datetime import datetime, timezone, timedelta
from os import path
from parameterized import parameterized

import configcatclient
from configcatclient import PollingMode, ConfigCatOptions, ConfigCatClient
from configcatclient.configcatoptions import Hooks
from configcatclient.localdictionarydatasource import LocalDictionaryFlagOverrides
from configcatclient.localfiledatasource import LocalFileDataSource
from configcatclient.logger import Logger
from configcatclient.overridedatasource import OverrideBehaviour
from configcatclient.rolloutevaluator import RolloutEvaluator
from configcatclient.user import User
import codecs

from configcatclient.utils import unicode_to_utf8
from configcatclienttests.mocks import MockLogHandler

logging.basicConfig(level=logging.WARNING)


class RolloutTests(unittest.TestCase):
    script_dir = path.dirname(__file__)
    value_test_type = "value_test"
    variation_test_type = "variation_test"

    def test_matrix_text(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d62463-86ec-8fde-f5b5-1c5c426fc830/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/AG6C1ngVb0CvM07un6JisQ', self.value_test_type)

    def test_matrix_semantic(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d745f1-f315-7daf-d163-5541d3786e6f/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix_semantic.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg', self.value_test_type)

    def test_matrix_semantic_2(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d77fa1-a796-85f9-df0c-57c448eb9934/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix_semantic_2.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/U8nt3zEhDEO5S2ulubCopA', self.value_test_type)

    def test_matrix_number(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d747f0-5986-c2ef-eef3-ec778e32e10a/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix_number.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw', self.value_test_type)

    def test_matrix_sensitive(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d7b724-9285-f4a7-9fcd-00f64f1e83d5/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix_sensitive.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/-0YmVOUNgEGKkgRF-rU65g', self.value_test_type)

    def test_matrix_comparators_v6(self):
        # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbc325-9a6b-4947-84e2-91529248278a/08dbc325-9ebd-4587-8171-88f76a3004cb
        self._test_matrix('data/testmatrix_comparators_v6.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ', self.value_test_type)

    def test_matrix_segments(self):
        # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbc325-9cfb-486f-8906-72a57c693615/08dbc325-9ebd-4587-8171-88f76a3004cb
        self._test_matrix('data/testmatrix_segments.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/h99HYXWWNE2bH8eWyLAVMA', self.value_test_type)

    def test_matrix_segments_old(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d9f207-6883-43e5-868c-cbf677af3fe6/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix_segments_old.csv',
                          'PKDVCLf-Hq-h-kCzMp-L7Q/LcYz135LE0qbcacz2mgXnA', self.value_test_type)

    def test_matrix_prerequisite_flag(self):
        # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbc325-9b74-45cb-86d0-4d61c25af1aa/08dbc325-9ebd-4587-8171-88f76a3004cb
        self._test_matrix('data/testmatrix_prerequisite_flag.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/JoGwdqJZQ0K2xDy7LnbyOg', self.value_test_type)

    def test_matrix_and_or(self):
        # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbc325-9d5e-4988-891c-fd4a45790bd1/08dbc325-9ebd-4587-8171-88f76a3004cb
        self._test_matrix('data/testmatrix_and_or.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/ByMO9yZNn02kXcm72lnY1A', self.value_test_type)

    def test_matrix_variation_id(self):
        # https://app.configcat.com/08d5a03c-feb7-af1e-a1fa-40b3329f8bed/08d774b9-3d05-0027-d5f4-3e76c3dba752/244cf8b0-f604-11e8-b543-f23c917f9d8d
        self._test_matrix('data/testmatrix_variationId.csv',
                          'PKDVCLf-Hq-h-kCzMp-L7Q/nQ5qkhRAUEa6beEyyrVLBA', self.variation_test_type)

    def test_matrix_unicode(self):
        # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbd63c-9774-49d6-8187-5f2aab7bd606/08dbc325-9ebd-4587-8171-88f76a3004cb
        self._test_matrix('data/testmatrix_unicode.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/Da6w8dBbmUeMUBhh0iEeQQ', self.value_test_type)

    def _test_matrix(self, file_path, sdk_key, type, base_url=None):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, file_path)

        # On Python 2.7, convert unicode to utf-8
        if sys.version_info[0] == 2:
            with codecs.open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                content = unicode_to_utf8(content)  # On Python 2.7, convert unicode to utf-8
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()

        # CSV header
        header = content[0].rstrip()
        setting_keys = header.split(';')[4:]
        custom_key = header.split(';')[3]
        content.pop(0)

        options = configcatclient.ConfigCatOptions(base_url=base_url)
        client = configcatclient.get(sdk_key, options)
        errors = ''
        for line in content:
            user_descriptor = line.rstrip().split(';')

            user_object = None
            if user_descriptor[0] is not None and user_descriptor[0] != '##null##':
                email = None
                country = None
                custom = None

                identifier = user_descriptor[0]

                if user_descriptor[1] is not None and user_descriptor[1] != '' and user_descriptor[1] != '##null##':
                    email = user_descriptor[1]

                if user_descriptor[2] is not None and user_descriptor[2] != '' and user_descriptor[2] != '##null##':
                    country = user_descriptor[2]

                if user_descriptor[3] is not None and user_descriptor[3] != '' and user_descriptor[3] != '##null##':
                    custom = {custom_key: user_descriptor[3]}

                user_object = User(identifier, email, country, custom)

            i = 0
            for setting_key in setting_keys:
                value = client.get_value_details(setting_key, None, user_object).variation_id if type == self.variation_test_type \
                    else client.get_value(setting_key, None, user_object)
                if str(value) != str(user_descriptor[i + 4]):
                    errors += 'Identifier: ' + user_descriptor[0] + '. SettingKey: ' + setting_key + \
                              '. Expected: ' + str(user_descriptor[i + 4]) + '. Result: ' + str(value) + '.\n'
                i += 1

        self.assertEqual('', errors)
        client.close()

    def test_wrong_user_object(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
        setting_value = client.get_value('stringContainsDogDefaultCat', 'Lion', {'Email': 'a@configcat.com'})
        self.assertEqual('Cat', setting_value)
        configcatclient.close_all()

    # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbc325-9e4e-4f59-86b2-5da50924b6ca/08dbc325-9ebd-4587-8171-88f76a3004cb
    @parameterized.expand([
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", None, None, None, "Cat", False, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", None, None, "Cat", False, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "a@example.com", None, "Dog", True, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "a@configcat.com", None, "Cat", False, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "a@configcat.com", "", "Frog", True, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "a@configcat.com", "US", "Fish", True, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "b@configcat.com", None, "Cat", False, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "b@configcat.com", "", "Falcon", False, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/P4e3fAz_1ky2-Zg2e4cbkw", "stringMatchedTargetingRuleAndOrPercentageOption", "12345", "b@configcat.com", "US", "Spider", False, True)
    ])
    def test_evaluation_details_matched_evaluation_rule_and_percentage_option(self, sdk_key, key, user_id, email, percentage_base, expected_return_value, expected_matched_targeting_rule, expected_matched_percentage_option):
        client = ConfigCatClient.get(sdk_key=sdk_key, options=ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        client.force_refresh()

        user = User(user_id, email=email, custom={"PercentageBase": percentage_base}) if user_id is not None else None

        evaluation_details = client.get_value_details(key, None, user)

        self.assertEqual(expected_return_value, evaluation_details.value)
        self.assertEqual(expected_matched_targeting_rule, evaluation_details.matched_targeting_rule is not None)
        self.assertEqual(expected_matched_percentage_option, evaluation_details.matched_percentage_option is not None)

    def test_user_object_attribute_value_conversion_text_comparison(self):
        client = ConfigCatClient.get(sdk_key='configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ',
                                     options=ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        client.force_refresh()

        logger = logging.getLogger('configcat')
        log_handler = MockLogHandler()
        logger.addHandler(log_handler)

        custom_attribute_name = 'Custom1'
        custom_attribute_value = 42
        user = User('12345', custom={custom_attribute_name: custom_attribute_value})

        key = 'boolTextEqualsNumber'
        value = client.get_value(key, None, user)

        self.assertEqual(True, value)

        self.assertEqual(1, len(log_handler.warning_logs))
        warning_log = log_handler.warning_logs[0]
        self.assertEqual("[3005] Evaluation of condition (User.%s EQUALS '%s') for setting '%s' may not produce the expected"
                         " result (the User.%s attribute is not a string value, thus it was automatically converted to the "
                         "string value '%s'). Please make sure that using a non-string value was intended." %
                         (custom_attribute_name, custom_attribute_value, key, custom_attribute_name, custom_attribute_value),
                         warning_log)

    @parameterized.expand([
        # SemVer-based comparisons
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", "0.0", "20%"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", "0.9.9", "< 1.0.0"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", "1.0.0", "20%"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", "1.1", "20%"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", 0, "20%"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", 0.9, "20%"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg", "lessThanWithPercentage", "12345", "Custom1", 2, "20%"),
        # Number-based comparisons
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", float('-inf'), "<2.1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", -1, "<2.1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", 2, "<2.1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", 2.1, "<=2,1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", 3, "<>4.2"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", 5, ">=5"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", float('inf'), ">5"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", float('nan'), "<>4.2"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "-inf", "<2.1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "-1", "<2.1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "2", "<2.1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "2.1", "<=2,1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "2,1", "<=2,1"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "3", "<>4.2"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "5", ">=5"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "inf", ">5"),
        ("configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw", "numberWithPercentage", "12345", "Custom1", "nan", "<>4.2"),
        # Date time-based comparisons
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 3, 31, 23, 59, 59, 999000), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 3, 31, 23, 59, 59, 999000, timezone.utc), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 4, 1, 1, 59, 59, 999000, timezone(timedelta(hours=2))), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 4, 1, 0, 0, 0, 1000, timezone.utc), True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 4, 1, 2, 0, 0, 1000, timezone(timedelta(hours=2))), True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 4, 30, 23, 59, 59, 999000, timezone.utc), True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 5, 1, 1, 59, 59, 999000, timezone(timedelta(hours=2))), True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 5, 1, 0, 0, 0, 1000, timezone.utc), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", datetime(2023, 5, 1, 2, 0, 0, 1000, timezone(timedelta(hours=2))), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", float('-inf'), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1680307199.999, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1680307200.001, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1682899199.999, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1682899200.001, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", float('inf'), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", float("nan"), False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1680307199, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1680307201, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1682899199, True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", 1682899201, False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "-inf", False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "1680307199.999", False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "1680307200.001", True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "1682899199.999", True),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "1682899200.001", False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "+inf", False),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "boolTrueIn202304", "12345", "Custom1", "NaN", False),
        # String array-based comparisons
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "stringArrayContainsAnyOfDogDefaultCat", "12345", "Custom1", ["x", "read"], "Dog"),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "stringArrayContainsAnyOfDogDefaultCat", "12345", "Custom1", ["x", "Read"], "Cat"),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "stringArrayContainsAnyOfDogDefaultCat", "12345", "Custom1", "[\"x\", \"read\"]", "Dog"),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "stringArrayContainsAnyOfDogDefaultCat", "12345", "Custom1", "[\"x\", \"Read\"]", "Cat"),
        ("configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ", "stringArrayContainsAnyOfDogDefaultCat", "12345", "Custom1", "x, read", "Cat")
    ])
    def test_user_object_attribute_value_conversion_non_text_comparisons(self, sdk_key, key, user_id, custom_attribute_name,
                                                                         custom_attribute_value, expected_return_value):
        client = ConfigCatClient.get(sdk_key=sdk_key,
                                     options=ConfigCatOptions(polling_mode=PollingMode.manual_poll()))
        client.force_refresh()
        user = User(user_id, custom={custom_attribute_name: custom_attribute_value})
        value = client.get_value(key, None, user)

        self.assertEqual(expected_return_value, value)

    @parameterized.expand([
        ("key1", "'key1' -> 'key1'"),
        ("key2", "'key2' -> 'key3' -> 'key2'"),
        ("key4", "'key4' -> 'key3' -> 'key2' -> 'key3'")
    ])
    def test_prerequisite_flag_circular_dependency(self, key, dependency_cycle):
        config = LocalFileDataSource(path.join(self.script_dir, 'data/test_circulardependency_v6.json'),
                                     OverrideBehaviour.LocalOnly, None).get_overrides()

        log = Logger('configcat', Hooks())
        logger = logging.getLogger('configcat')
        log_handler = MockLogHandler()
        logger.addHandler(log_handler)
        evaluator = RolloutEvaluator(log)

        value, _, _, _, _ = evaluator.evaluate(key, None, 'default_value', 'default_variation_id', config, None)

        self.assertEqual('default_value', value)
        error_log = log_handler.error_logs[0]
        self.assertTrue('Circular dependency detected' in error_log)
        self.assertTrue(dependency_cycle in error_log)

    @parameterized.expand([
        ("stringDependsOnBool", "mainBoolFlag", True, "Dog"),
        ("stringDependsOnBool", "mainBoolFlag", False, "Cat"),
        ("stringDependsOnBool", "mainBoolFlag", "1", None),
        ("stringDependsOnBool", "mainBoolFlag", 1, None),
        ("stringDependsOnBool", "mainBoolFlag", 1.0, None),
        ("stringDependsOnBool", "mainBoolFlag", [True], None),
        ("stringDependsOnBool", "mainBoolFlag", None, None),
        ("stringDependsOnString", "mainStringFlag", "private", "Dog"),
        ("stringDependsOnString", "mainStringFlag", "Private", "Cat"),
        ("stringDependsOnString", "mainStringFlag", True, None),
        ("stringDependsOnString", "mainStringFlag", 1, None),
        ("stringDependsOnString", "mainStringFlag", 1.0, None),
        ("stringDependsOnString", "mainStringFlag", ["private"], None),
        ("stringDependsOnString", "mainStringFlag", None, None),
        ("stringDependsOnInt", "mainIntFlag", 2, "Dog"),
        ("stringDependsOnInt", "mainIntFlag", 1, "Cat"),
        ("stringDependsOnInt", "mainIntFlag", "2", None),
        ("stringDependsOnInt", "mainIntFlag", True, None),
        ("stringDependsOnInt", "mainIntFlag", 2.0, None),
        ("stringDependsOnInt", "mainIntFlag", [2], None),
        ("stringDependsOnInt", "mainIntFlag", None, None),
        ("stringDependsOnDouble", "mainDoubleFlag", 0.1, "Dog"),
        ("stringDependsOnDouble", "mainDoubleFlag", 0.11, "Cat"),
        ("stringDependsOnDouble", "mainDoubleFlag", "0.1", None),
        ("stringDependsOnDouble", "mainDoubleFlag", True, None),
        ("stringDependsOnDouble", "mainDoubleFlag", 1, None),
        ("stringDependsOnDouble", "mainDoubleFlag", [0.1], None),
        ("stringDependsOnDouble", "mainDoubleFlag", None, None)
    ])
    def test_prerequisite_flag_comparison_value_type_mismatch(self, key, prerequisite_flag_key, prerequisite_flag_value, expected_value):
        override_dictionary = {prerequisite_flag_key: prerequisite_flag_value}
        options = ConfigCatOptions(polling_mode=PollingMode.manual_poll(),
                                   flag_overrides=LocalDictionaryFlagOverrides(
                                       source=override_dictionary,
                                       override_behaviour=OverrideBehaviour.LocalOverRemote))
        client = ConfigCatClient.get(sdk_key='configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/JoGwdqJZQ0K2xDy7LnbyOg', options=options)
        client.force_refresh()

        logger = logging.getLogger('configcat')
        log_handler = MockLogHandler()
        logger.addHandler(log_handler)

        value = client.get_value(key, None)

        self.assertEqual(expected_value, value)

        if expected_value is None:
            self.assertEqual(1, len(log_handler.error_logs))
            error_log = log_handler.error_logs[0]
            self.assertTrue('Type mismatch between comparison value' in error_log)
            self.assertTrue('and prerequisite flag' in error_log)

        client.close()


'''
    def test_create_matrix_text(self):
        self._test_create_matrix('data/testmatrix.csv', 'data/testmatrix_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
    
    def test_create_matrix_semantic(self):
        self._test_create_matrix('data/testmatrix_semantic.csv', 'data/testmatrix_semantic_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/BAr3KgLTP0ObzKnBTo5nhA')

    def test_create_matrix_semnatic_2(self):
        self._test_create_matrix('data/testmatrix_input_semantic_2.csv', 'data/testmatrix_semantic_2.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/q6jMCFIp-EmuAfnmZhPY7w')

    def test_create_matrix_number(self):
        self._test_create_matrix('data/testmatrix_number.csv', 'data/testmatrix_number_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/uGyK3q9_ckmdxRyI7vjwCw')

    def _test_create_matrix(self, file_path, out_file_path, sdk_key):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, file_path)
        out_file_path = path.join(script_dir, out_file_path)

        with open(file_path, 'r') as f:
            content = f.readlines()

        # CSV header
        header = content[0].rstrip()
        setting_keys = header.split(';')[4:]
        custom_attribute = header.split(';')[3]
        content.pop(0)

        client = configcatclient.create_client(sdk_key)
        with open(out_file_path, 'w') as f:
            f.writelines(header + '\n')

            for line in content:
                user_descriptor = line.rstrip().split(';')[:4]
                user_object = None
                if user_descriptor[0] is not None and user_descriptor[0] != '##null##':
                    identifier = user_descriptor[0]
                     
                    email = None
                    if user_descriptor[1] is not None and user_descriptor[1] != '' and user_descriptor[1] != '##null##':
                        email = user_descriptor[1]
                        
                    country = None
                    if user_descriptor[2] is not None and user_descriptor[2] != '' and user_descriptor[2] != '##null##':
                        country = user_descriptor[2]
                        
                    custom = None
                    if user_descriptor[3] is not None and user_descriptor[3] != '' and user_descriptor[3] != '##null##':
                        custom = {custom_attribute: user_descriptor[3]}
                    
                    user_object = User(identifier, email, country, custom)

                for setting_key in setting_keys:
                    value = client.get_value(setting_key, None, user_object)
                    user_descriptor.append(str(value))

                f.writelines(';'.join(user_descriptor) + '\n')
'''
