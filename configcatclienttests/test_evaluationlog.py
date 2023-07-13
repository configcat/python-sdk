import logging
import unittest
import re

import configcatclient
from configcatclient.user import User

logging.basicConfig(level=logging.INFO)

TARGETING_IS_NOT_POSSIBLE_NO_USER = "[3001] Cannot evaluate targeting rules and % options for setting '{}' " \
                                    "(User Object is missing). You should pass a User Object to the evaluation " \
                                    "methods like `get_value()` in order to make targeting work properly. " \
                                    "Read more: https://configcat.com/docs/advanced/user-object/"

OPTIONS_IS_NOT_POSSIBLE_NO_USER = "[3001] Cannot evaluate % options for setting '{}' " \
                                  "(User Object is missing). You should pass a User Object to the evaluation " \
                                  "methods like `get_value()` in order to make targeting work properly. " \
                                  "Read more: https://configcat.com/docs/advanced/user-object/"

class MockLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(MockLogHandler, self).__init__(*args, **kwargs)
        self.error_logs = []
        self.warning_logs = []
        self.info_logs = []

    def clear(self):
        self.error_logs = []
        self.warning_logs = []
        self.info_logs = []

    def emit(self, record):
        if record.levelno == logging.ERROR:
            self.error_logs.append(record.getMessage())
        elif record.levelno == logging.WARNING:
            self.warning_logs.append(record.getMessage())
        elif record.levelno == logging.INFO:
            self.info_logs.append(record.getMessage())


# Remove the u prefix from unicode strings on python 2.7. When we only support python 3 this can be removed.
def remove_unicode_prefix(string):
    return re.sub(r"u'(.*?)'", r"'\1'", string)


class EvaluationLogTests(unittest.TestCase):

    def setUp(self):
        self.log_handler = MockLogHandler()
        logger = logging.getLogger('configcat')
        logger.setLevel(logging.INFO)
        logger.addHandler(self.log_handler)

    def test_simple_value(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

        client.get_value('boolDefaultFalse', True)
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'boolDefaultFalse'\n"
            "  Returning 'False'."
        )
        self.log_handler.clear()

        client.get_value('boolDefaultTrue', False)
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'boolDefaultTrue'\n"
            "  Returning 'True'."
        )
        self.log_handler.clear()

        client.get_value('stringDefaultCat', 'Default')
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'stringDefaultCat'\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('integerDefaultOne', 0)
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'integerDefaultOne'\n"
            "  Returning '1'."
        )
        self.log_handler.clear()

        client.get_value('doubleDefaultPi', 0)
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'doubleDefaultPi'\n"
            "  Returning '3.1415'."
        )
        self.log_handler.clear()

        client.close()

    def test_1_targeting_rule(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

        client.get_value('stringContainsDogDefaultCat', False)
        self.assertEqual(
            self.log_handler.warning_logs[0],
            TARGETING_IS_NOT_POSSIBLE_NO_USER.format('stringContainsDogDefaultCat')
        )
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            "[5000] Evaluating 'stringContainsDogDefaultCat'\n"
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN 'Dog' => cannot evaluate, User Object is missing\n"
            "    The current targeting rule is ignored and the evaluation continues with the next rule.\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('stringContainsDogDefaultCat', False, User('12345'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'stringContainsDogDefaultCat\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": null}\'\n'
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN 'Dog' => no match\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('stringContainsDogDefaultCat', False, User('12345', email='joe@example.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'stringContainsDogDefaultCat\' for User \'{"Identifier": "12345", "Email": "joe@example.com", "Country": null, "Custom": null}\'\n'
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN 'Dog' => no match\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('stringContainsDogDefaultCat', False, User('12345', email='joe@configcat.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'stringContainsDogDefaultCat\' for User \'{"Identifier": "12345", "Email": "joe@configcat.com", "Country": null, "Custom": null}\'\n'
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN 'Dog' => MATCH, applying rule\n"
            "  Returning 'Dog'."
        )
        self.log_handler.clear()

        client.close()

    def test_2_targeting_rules(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

        client.get_value('stringIsInDogDefaultCat', False)
        self.assertEqual(
            self.log_handler.warning_logs[0],
            TARGETING_IS_NOT_POSSIBLE_NO_USER.format('stringIsInDogDefaultCat')
        )
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            "[5000] Evaluating 'stringIsInDogDefaultCat'\n"
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email IS ONE OF (hashed) ['a79a58142e...', '8af1824d6c...'] THEN 'Dog' => cannot evaluate, User Object is missing\n"
            "    The current targeting rule is ignored and the evaluation continues with the next rule.\n"
            "  - IF User.Custom1 IS ONE OF (hashed) ['e01dfbe824...'] THEN 'Dog' => cannot evaluate, User Object is missing\n"
            "    The current targeting rule is ignored and the evaluation continues with the next rule.\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('stringIsInDogDefaultCat', False, User('12345'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'stringIsInDogDefaultCat\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": null}\'\n'
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email IS ONE OF (hashed) ['a79a58142e...', '8af1824d6c...'] THEN 'Dog' => no match\n"
            "  - IF User.Custom1 IS ONE OF (hashed) ['e01dfbe824...'] THEN 'Dog' => no match\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('stringIsInDogDefaultCat', False, User('12345', custom={'Custom1': 'user'}))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'stringIsInDogDefaultCat\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": {"Custom1": "user"}}\'\n'
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email IS ONE OF (hashed) ['a79a58142e...', '8af1824d6c...'] THEN 'Dog' => no match\n"
            "  - IF User.Custom1 IS ONE OF (hashed) ['e01dfbe824...'] THEN 'Dog' => no match\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('stringIsInDogDefaultCat', False, User('12345', custom={'Custom1': 'admin'}))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'stringIsInDogDefaultCat\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": {"Custom1": "admin"}}\'\n'
            "  Evaluating targeting rules and applying the first match if any:\n"
            "  - IF User.Email IS ONE OF (hashed) ['a79a58142e...', '8af1824d6c...'] THEN 'Dog' => no match\n"
            "  - IF User.Custom1 IS ONE OF (hashed) ['e01dfbe824...'] THEN 'Dog' => MATCH, applying rule\n"
            "  Returning 'Dog'."
        )
        self.log_handler.clear()

        client.close()

    def test_options_based_on_user_id(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

        client.get_value('string75Cat0Dog25Falcon0Horse', False)
        self.assertEqual(
            self.log_handler.warning_logs[0],
            OPTIONS_IS_NOT_POSSIBLE_NO_USER.format('string75Cat0Dog25Falcon0Horse')
        )
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'string75Cat0Dog25Falcon0Horse'\n"
            "  Skipping % options because the User Object is missing.\n"
            "  Returning 'Chicken'."
        )
        self.log_handler.clear()

        client.get_value('string75Cat0Dog25Falcon0Horse', False, User('12345'))
        self.assertEqual(
            self.log_handler.info_logs[0],
            '[5000] Evaluating \'string75Cat0Dog25Falcon0Horse\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": null}\'\n'
            "  Evaluating % options based on the User.Identifier attribute:\n"
            "  - Computing hash in the [0..99] range from User.Identifier => 21 (this value is sticky and consistent across all SDKs)\n"
            "  - Hash value 21 selects % option 1 (75%), 'Cat'\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.close()

    def test_options_based_on_custom_attr(self):
        client = configcatclient.get(
            'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/x0tcrFMkl02A65D8GD20Eg',
            configcatclient.ConfigCatOptions(base_url='https://test-cdn-eu.configcat.com')
        )

        client.get_value('string75Cat0Dog25Falcon0HorseCustomAttr', 'default')
        self.assertEqual(
            self.log_handler.warning_logs[0],
            OPTIONS_IS_NOT_POSSIBLE_NO_USER.format('string75Cat0Dog25Falcon0HorseCustomAttr')
        )
        self.assertEqual(
            self.log_handler.info_logs[0],
            "[5000] Evaluating 'string75Cat0Dog25Falcon0HorseCustomAttr'\n"
            "  Skipping % options because the User Object is missing.\n"
            "  Returning 'Chicken'."
        )
        self.log_handler.clear()

        client.get_value('string75Cat0Dog25Falcon0HorseCustomAttr', 'default', User('12345'))
        self.assertEqual(
            self.log_handler.info_logs[0],
            '[5000] Evaluating \'string75Cat0Dog25Falcon0HorseCustomAttr\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": null}\'\n'
            '  Skipping % options because the User.Country attribute is missing.\n'
            '  The current targeting rule is ignored and the evaluation continues with the next rule.\n' # FIXME: is this line needed?
            "  Returning 'Chicken'."
        )
        self.log_handler.clear()

        client.get_value('string75Cat0Dog25Falcon0HorseCustomAttr', 'default', User('12345', country='US'))
        self.assertEqual(
            self.log_handler.info_logs[0],
            '[5000] Evaluating \'string75Cat0Dog25Falcon0HorseCustomAttr\' for User \'{"Identifier": "12345", "Email": null, "Country": "US", "Custom": null}\'\n'
            '  Evaluating % options based on the User.Country attribute:\n'
            '  - Computing hash in the [0..99] range from User.Country => 70 (this value is sticky and consistent across all SDKs)\n'
            "  - Hash value 70 selects % option 1 (75%), 'Cat'\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.close()

    def test_options_after_targeting_rule(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

        client.get_value('integer25One25Two25Three25FourAdvancedRules', 42)
        self.assertEqual(
            self.log_handler.warning_logs[0],
            TARGETING_IS_NOT_POSSIBLE_NO_USER.format('integer25One25Two25Three25FourAdvancedRules')
        )
        self.assertEqual(
            self.log_handler.warning_logs[1],
            OPTIONS_IS_NOT_POSSIBLE_NO_USER.format('integer25One25Two25Three25FourAdvancedRules')
        )
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            "[5000] Evaluating 'integer25One25Two25Three25FourAdvancedRules'\n"
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN '5' => cannot evaluate, User Object is missing\n"
            '    The current targeting rule is ignored and the evaluation continues with the next rule.\n'
            '  Skipping % options because the User Object is missing.\n'
            "  Returning '-1'."
        )
        self.log_handler.clear()

        client.get_value('integer25One25Two25Three25FourAdvancedRules', 42, User('12345'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'integer25One25Two25Three25FourAdvancedRules\' for User \'{"Identifier": "12345", "Email": null, "Country": null, "Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN '5' => no match\n"
            '  Evaluating % options based on the User.Identifier attribute:\n'
            '  - Computing hash in the [0..99] range from User.Identifier => 25 (this value is sticky and consistent across all SDKs)\n'
            "  - Hash value 25 selects % option 2 (50%), '2'\n"
            "  Returning '2'."
        )
        self.log_handler.clear()

        client.get_value('integer25One25Two25Three25FourAdvancedRules', 42, User('12345', email='joe@example.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'integer25One25Two25Three25FourAdvancedRules\' for User \'{"Identifier": "12345", "Email": "joe@example.com", "Country": null, "Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN '5' => no match\n"
            '  Evaluating % options based on the User.Identifier attribute:\n'
            '  - Computing hash in the [0..99] range from User.Identifier => 25 (this value is sticky and consistent across all SDKs)\n'
            "  - Hash value 25 selects % option 2 (50%), '2'\n"
            "  Returning '2'."
        )
        self.log_handler.clear()

        client.get_value('integer25One25Two25Three25FourAdvancedRules', 42, User('12345', email='joe@configcat.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'integer25One25Two25Three25FourAdvancedRules\' for User \'{"Identifier": "12345", "Email": "joe@configcat.com", "Country": null, '
            '"Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User.Email CONTAINS ANY OF ['@configcat.com'] THEN '5' => MATCH, applying rule\n"
            "  Returning '5'."
        )
        self.log_handler.clear()

        client.close()

    def test_and_rules(self):
        client = configcatclient.get(
            'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/FfwncdJg1kq0lBqxhYC_7g',
            configcatclient.ConfigCatOptions(base_url='https://test-cdn-eu.configcat.com')
        )

        client.get_value('emailAnd', 'default')
        self.assertEqual(
            self.log_handler.warning_logs[0],
            TARGETING_IS_NOT_POSSIBLE_NO_USER.format('emailAnd')
        )
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            "[5000] Evaluating 'emailAnd'\n"
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User.Email STARTS WITH ANY OF (hashed) ['4_82d1be67...'] => False, skipping the remaining AND conditions\n"
            "    THEN 'Dog' => cannot evaluate, User Object is missing\n"
            '    The current targeting rule is ignored and the evaluation continues with the next rule.\n'
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.get_value('emailAnd', 'default', User('12345', email='jane@example.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'emailAnd\' for User \'{"Identifier": "12345", "Email": "jane@example.com", "Country": null, "Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User.Email STARTS WITH ANY OF (hashed) ['4_82d1be67...'] => True\n"
            "    AND User.Email CONTAINS ANY OF ['@'] => True\n"
            "    AND User.Email ENDS WITH (hashed) ['20_1d54924...'] => False, skipping the remaining AND conditions\n"
            "    THEN 'Dog' => no match\n"
            "  Returning 'Cat'."
        )
        self.log_handler.clear()

        client.close()

    def test_segment(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/LcYz135LE0qbcacz2mgXnA')

        client.get_value('featureWithSegmentTargeting', False)
        self.assertEqual(
            self.log_handler.warning_logs[0],
            TARGETING_IS_NOT_POSSIBLE_NO_USER.format('featureWithSegmentTargeting')
        )
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            "[5000] Evaluating 'featureWithSegmentTargeting'\n"
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User IS IN SEGMENT 'Beta users' THEN 'True' => cannot evaluate, User Object is missing\n"
            '    The current targeting rule is ignored and the evaluation continues with the next rule.\n'
            "  Returning 'False'."
        )
        self.log_handler.clear()

        client.get_value('featureWithSegmentTargeting', False, User('12345', email='jane@example.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'featureWithSegmentTargeting\' for User \'{"Identifier": "12345", "Email": "jane@example.com", "Country": null, "Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User IS IN SEGMENT 'Beta users'\n"
            '    (\n'
            "      Evaluating segment 'Beta users':\n"
            "      - IF User.Email IS ONE OF (hashed) ['26fc71b9ce...', 'daaa967a93...'] => True\n"
            '      Segment evaluation result: User IS IN SEGMENT.\n'
            "      Condition (User IS IN SEGMENT 'Beta users') evaluates to True.\n"
            '    )\n'
            "    THEN 'True' => MATCH, applying rule\n"
            "  Returning 'True'."
        )
        self.log_handler.clear()

        client.get_value('featureWithNegatedSegmentTargeting', False, User('12345', email='jane@example.com'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'featureWithNegatedSegmentTargeting\' for User \'{"Identifier": "12345", "Email": "jane@example.com", "Country": null, "Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF User IS NOT IN SEGMENT 'Beta users'\n"
            '    (\n'
            "      Evaluating segment 'Beta users':\n"
            "      - IF User.Email IS ONE OF (hashed) ['26fc71b9ce...', 'daaa967a93...'] => True\n"
            '      Segment evaluation result: User IS IN SEGMENT.\n'
            "      Condition (User IS NOT IN SEGMENT 'Beta users') evaluates to False.\n"
            '    )\n'
            "    THEN 'True' => no match\n"
            "  Returning 'False'."
        )
        self.log_handler.clear()

        client.close()

    def test_prerequisite_flag(self):
        client = configcatclient.get(
            'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/FfwncdJg1kq0lBqxhYC_7g',
            configcatclient.ConfigCatOptions(base_url='https://test-cdn-eu.configcat.com')
        )

        client.get_value('dependentFeature', 'default', User('12345', email='kate@configcat.com', country='USA'))
        self.assertEqual(
            remove_unicode_prefix(self.log_handler.info_logs[0]),
            '[5000] Evaluating \'dependentFeature\' for User \'{"Identifier": "12345", "Email": "kate@configcat.com", "Country": "USA", "Custom": null}\'\n'
            '  Evaluating targeting rules and applying the first match if any:\n'
            "  - IF flag 'mainFeature' EQUALS 'target'\n"
            "    (\n"
            "      Evaluating prerequisite flag 'mainFeature':\n"
            "      Evaluating targeting rules and applying the first match if any:\n"
            "      - IF User.Email ENDS WITH (hashed) ['21_ff4f72a...'] => False, skipping the remaining AND conditions\n"
            "        THEN 'private' => no match\n"
            "      - IF User.Country IS ONE OF (hashed) ['391ea48edd...'] => True\n"
            "        AND User IS NOT IN SEGMENT 'Beta'\n"
            "        (\n"
            "          Evaluating segment 'Beta':\n"
            "          - IF User.Email IS ONE OF (hashed) ['8ce91ec158...', '45086cef41...'] => False, skipping the remaining AND conditions\n"
            "          Segment evaluation result: User IS NOT IN SEGMENT.\n"
            "          Condition (User IS NOT IN SEGMENT 'Beta') evaluates to True.\n"
            "        ) => True\n"
            "        AND User IS NOT IN SEGMENT 'Deve'\n"
            "        (\n"
            "          Evaluating segment 'Deve':\n"
            "          - IF User.Email IS ONE OF (hashed) ['4c87c42ca5...', '5f7e0f5f0f...'] => False, skipping the remaining AND conditions\n"
            "          Segment evaluation result: User IS NOT IN SEGMENT.\n"
            "          Condition (User IS NOT IN SEGMENT 'Deve') evaluates to True.\n"
            "        ) => True\n"
            "        THEN 'target' => MATCH, applying rule\n"
            "      Prerequisite flag evaluation result: 'target'\n"
            "      Condition: (Flag 'mainFeature' EQUALS 'target') evaluates to True.\n"
            "    )\n"
            "    THEN % option => MATCH, applying rule\n"
            "  Evaluating % options based on the User.Identifier attribute:\n"
            "  - Computing hash in the [0..99] range from User.Identifier => 78 (this value is sticky and consistent across all SDKs)\n"
            "  - Hash value 78 selects % option 4 (100%), 'Horse'\n"
            "  Returning 'Horse'."
        )
        self.log_handler.clear()

        client.close()


if __name__ == '__main__':
    unittest.main()
