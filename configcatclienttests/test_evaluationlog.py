import json
import logging
import os
import unittest
import re
import sys

try:
    from cStringIO import StringIO  # Python 2.7
except ImportError:
    from io import StringIO

from configcatclient import ConfigCatClient, ConfigCatOptions, PollingMode
from configcatclient.localfiledatasource import LocalFileFlagOverrides
from configcatclient.overridedatasource import OverrideBehaviour
from configcatclient.user import User
from configcatclienttests.mocks import TEST_SDK_KEY

logging.basicConfig(level=logging.INFO)


# Remove the u prefix from unicode strings on python 2.7. When we only support python 3 this can be removed.
def remove_unicode_prefix(string):
    return re.sub(r"u'(.*?)'", r"'\1'", string)


class EvaluationLogTests(unittest.TestCase):
    def test_simple_value(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/simple_value.json'))

    def test_1_targeting_rule(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/1_targeting_rule.json'))

    def test_2_targeting_rules(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/2_targeting_rules.json'))

    def test_options_based_on_user_id(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/options_based_on_user_id.json'))

    def test_options_based_on_custom_attr(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/options_based_on_custom_attr.json'))

    def test_options_after_targeting_rule(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/options_after_targeting_rule.json'))

    def test_options_within_targeting_rule(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/options_within_targeting_rule.json'))

    def test_and_rules(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/and_rules.json'))

    def test_segment(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/segment.json'))

    def test_prerequisite_flag(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/prerequisite_flag.json'))

    def test_semver_validation(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/semver_validation.json'))

    def test_epoch_date_validation(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/epoch_date_validation.json'))

    def test_number_validation(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/number_validation.json'))

    def test_comparators_validation(self):
        self.maxDiff = None
        self.assertTrue(self._test_evaluation_log('data/evaluation/comparators.json'))

    def test_list_truncation_validation(self):
        self.assertTrue(self._test_evaluation_log('data/evaluation/list_truncation.json'))

    def _test_evaluation_log(self, file_path, test_filter=None, generate_expected_log=False):
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, file_path)
        self.assertTrue(os.path.isfile(file_path))
        name = os.path.basename(file_path)[:-5]
        file_dir = os.path.join(os.path.dirname(file_path), name)

        with open(file_path, 'r') as f:
            data = json.load(f)
            sdk_key = data.get('sdkKey')
            base_url = data.get('baseUrl')
            json_override = data.get('jsonOverride')
            flag_overrides = None
            if json_override:
                flag_overrides = LocalFileFlagOverrides(
                    file_path=os.path.join(file_dir, json_override),
                    override_behaviour=OverrideBehaviour.LocalOnly
                )
                if not sdk_key:
                    sdk_key = TEST_SDK_KEY

            client = ConfigCatClient.get(sdk_key, ConfigCatOptions(
                polling_mode=PollingMode.manual_poll(),
                flag_overrides=flag_overrides,
                base_url=base_url
            ))
            client.force_refresh()

            # setup logging
            log_stream = StringIO()
            log_handler = logging.StreamHandler(log_stream)
            log_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
            logger = logging.getLogger('configcat')
            logger.setLevel(logging.INFO)
            logger.addHandler(log_handler)

            for test in data['tests']:
                key = test.get('key')
                default_value = test.get('defaultValue')
                return_value = test.get('returnValue')
                user = test.get('user')
                expected_log_file = test.get('expectedLog')
                test_name = expected_log_file[:-4]

                # apply test filter
                if test_filter and test_name not in test_filter:
                    continue

                expected_log_file_path = os.path.join(file_dir, expected_log_file)
                user_object = None
                if user:
                    custom = {k: v for k, v in user.items() if k not in {'Identifier', 'Email', 'Country'}}
                    if len(custom) == 0:
                        custom = None
                    user_object = User(user.get('Identifier'), user.get('Email'), user.get('Country'), custom)

                # clear log
                log_stream.seek(0)
                log_stream.truncate()

                value = client.get_value(key, default_value, user_object)
                log = remove_unicode_prefix(log_stream.getvalue())

                if generate_expected_log:
                    # create directory if needed
                    if not os.path.exists(file_dir):
                        os.makedirs(file_dir)

                    with open(expected_log_file_path, 'w') as file:
                        file.write(log)
                else:
                    self.assertTrue(os.path.isfile(expected_log_file_path))
                    with open(expected_log_file_path, 'r') as file:
                        expected_log = file.read()

                    # On <= Python 3.5 the order of the keys in the serialized user object is random.
                    # We need to cut out the JSON part and compare the JSON objects separately.
                    if sys.version_info[:2] <= (3, 5):
                        if expected_log.startswith('INFO [5000]') and log.startswith('INFO [5000]'):
                            # Extract the JSON part from expected_log
                            match = re.search(r'(\{.*?\})', expected_log)
                            expected_log_json = None
                            if match:
                                expected_log_json = json.loads(match.group(1))
                                # Remove the JSON-like part from the original string
                                expected_log = re.sub(r'\{.*?\}', '', expected_log)

                            # Extract the JSON part from log
                            log_json = None
                            match = re.search(r'(\{.*?\})', log)
                            if match:
                                log_json = json.loads(match.group(1))
                                # Remove the JSON-like part from the original string
                                log = re.sub(r'\{.*?\}', '', log)

                            self.assertEqual(expected_log_json, log_json, 'User object mismatch for test: ' + test_name)

                    self.assertEqual(expected_log, log, 'Log mismatch for test: ' + test_name)
                    self.assertEqual(return_value, value, 'Return value mismatch for test: ' + test_name)

            client.close()
            return True

        return False


'''
    def test_generate_all_evaluation_logs(self):
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, 'data/evaluation')
        self.assertTrue(os.path.isdir(file_path))
        for file in os.listdir(file_path):
            if file.endswith('.json'):
                self._evaluation_log(os.path.join('data/evaluation', file), generate_expected_log=True)
'''


if __name__ == '__main__':
    unittest.main()
