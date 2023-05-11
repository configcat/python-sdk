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
        self._test_matrix('./testmatrix.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A', self.value_test_type)

    def test_matrix_semantic(self):
        self._test_matrix('./testmatrix_semantic.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/BAr3KgLTP0ObzKnBTo5nhA', self.value_test_type)

    def test_matrix_semantic_2(self):
        self._test_matrix('./testmatrix_semantic_2.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/q6jMCFIp-EmuAfnmZhPY7w', self.value_test_type)

    def test_matrix_number(self):
        self._test_matrix('./testmatrix_number.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/uGyK3q9_ckmdxRyI7vjwCw', self.value_test_type)

    def test_matrix_sensitive(self):
        self._test_matrix('./testmatrix_sensitive.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/qX3TP2dTj06ZpCCT1h_SPA', self.value_test_type)

    def test_matrix_comparators_v6(self):
        self._test_matrix('./testmatrix_comparators_v6.csv',
                          'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/Lv2mD9Tgx0Km27nuHjw_FA',
                          self.value_test_type, base_url='https://test-cdn-global.configcat.com')

    def test_matrix_segments(self):
        self._test_matrix('./testmatrix_segments.csv',
                          'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/LP0_4hhbQkmVVJcsbO_2Lw',
                          self.value_test_type, base_url='https://test-cdn-global.configcat.com')

    def test_matrix_dependent_flag(self):
        self._test_matrix('./testmatrix_dependent_flag.csv',
                          'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/LGO_8DM9OUGpJixrqqqQcA',
                          self.value_test_type, base_url='https://test-cdn-global.configcat.com')

    def test_matrix_and_or(self):
        self._test_matrix('./testmatrix_and_or.csv',
                          'configcat-sdk-1/XUbbCFZX_0mOU_uQ_XYGMg/FfwncdJg1kq0lBqxhYC_7g',
                          self.value_test_type, base_url='https://test-cdn-global.configcat.com')

    def test_matrix_variation_id(self):
        self._test_matrix('./testmatrix_variationId.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/nQ5qkhRAUEa6beEyyrVLBA', self.variation_test_type)

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
                value = client.get_variation_id(setting_key, None, user_object) if type == self.variation_test_type \
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
        self._test_create_matrix('./testmatrix.csv', './testmatrix_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
    
    def test_create_matrix_semantic(self):
        self._test_create_matrix('./testmatrix_semantic.csv', './testmatrix_semantic_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/BAr3KgLTP0ObzKnBTo5nhA')

    def test_create_matrix_semnatic_2(self):
        self._test_create_matrix('./testmatrix_input_semantic_2.csv', './testmatrix_semantic_2.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/q6jMCFIp-EmuAfnmZhPY7w')

    def test_create_matrix_number(self):
        self._test_create_matrix('./testmatrix_number.csv', './testmatrix_number_out.csv',
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
