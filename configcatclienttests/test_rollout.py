import logging
import sys
import unittest
from os import path

import configcatclient
from configcatclient import PollingMode
from configcatclient.user import User
import codecs

from configcatclient.utils import unicode_to_utf8

logging.basicConfig(level=logging.WARNING)


class RolloutTests(unittest.TestCase):

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
