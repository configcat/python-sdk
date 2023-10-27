import logging
import unittest
from os import path

import configcatclient
from configcatclient.user import User

logging.basicConfig(level=logging.WARNING)


class RolloutTests(unittest.TestCase):

    value_test_type = "value_test"
    variation_test_type = "variation_test"

    def test_matrix_text(self):
        self._test_matrix('data/testmatrix.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/AG6C1ngVb0CvM07un6JisQ', self.value_test_type)

    def test_matrix_semantic(self):
        self._test_matrix('data/testmatrix_semantic.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/iV8vH2MBakKxkFZylxHmTg', self.value_test_type)

    def test_matrix_semantic_2(self):
        self._test_matrix('data/testmatrix_semantic_2.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/U8nt3zEhDEO5S2ulubCopA', self.value_test_type)

    def test_matrix_number(self):
        self._test_matrix('data/testmatrix_number.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/FCWN-k1dV0iBf8QZrDgjdw', self.value_test_type)

    def test_matrix_sensitive(self):
        self._test_matrix('data/testmatrix_sensitive.csv',
                          'configcat-sdk-1/PKDVCLf-Hq-h-kCzMp-L7Q/-0YmVOUNgEGKkgRF-rU65g', self.value_test_type)

    def test_matrix_comparators_v6(self):
        self._test_matrix('data/testmatrix_comparators_v6.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/OfQqcTjfFUGBwMKqtyEOrQ', self.value_test_type)

    def test_matrix_segments(self):
        self._test_matrix('data/testmatrix_segments.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/h99HYXWWNE2bH8eWyLAVMA', self.value_test_type)

    def test_matrix_prerequisite_flag(self):
        self._test_matrix('data/testmatrix_prerequisite_flag.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/JoGwdqJZQ0K2xDy7LnbyOg', self.value_test_type)

    def test_matrix_and_or(self):
        self._test_matrix('data/testmatrix_and_or.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/ByMO9yZNn02kXcm72lnY1A', self.value_test_type)

    def test_matrix_variation_id(self):
        self._test_matrix('data/testmatrix_variationId.csv',
                          'PKDVCLf-Hq-h-kCzMp-L7Q/nQ5qkhRAUEa6beEyyrVLBA', self.variation_test_type)

    def test_matrix_unicode(self):
        # https://app.configcat.com/v2/e7a75611-4256-49a5-9320-ce158755e3ba/08dbc325-7f69-4fd4-8af4-cf9f24ec8ac9/08dbd63c-9774-49d6-8187-5f2aab7bd606/08dbc325-9ebd-4587-8171-88f76a3004cb
        self._test_matrix('data/testmatrix_unicode.csv',
                          'configcat-sdk-1/JcPbCGl_1E-K9M-fJOyKyQ/Da6w8dBbmUeMUBhh0iEeQQ', self.value_test_type)

    def _test_matrix(self, file_path, sdk_key, type, base_url=None):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, file_path)

        with open(file_path, 'r') as f:
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
