import unittest
from os import path

import configcatclient
from configcatclient.interfaces import LogLevel
from configcatclient.user import User


class RolloutTests(unittest.TestCase):

    def test_matrix_text(self):
        self._test_matrix('./testmatrix.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

    def test_matrix_semantic(self):
        self._test_matrix('./testmatrix_semantic.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/BAr3KgLTP0ObzKnBTo5nhA')

    def test_matrix_number(self):
        self._test_matrix('./testmatrix_number.csv', 'PKDVCLf-Hq-h-kCzMp-L7Q/uGyK3q9_ckmdxRyI7vjwCw')

    def _test_matrix(self, file_path, api_key):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, file_path)

        with open(file_path, 'r') as f:
            content = f.readlines()

        # CSV header
        header = content[0].rstrip()
        setting_keys = header.split(';')[4:]
        content.pop(0)

        client = configcatclient.create_client(api_key)
        client.set_log_level(LogLevel.INFO)
        errors = ''
        for line in content:
            user_descriptor = line.rstrip().split(';')

            user_object = None
            if user_descriptor[0] is not None and user_descriptor[0] != '' and user_descriptor[0] != '##null##':
                email = None
                country = None
                custom = None

                identifier = user_descriptor[0]

                if user_descriptor[1] is not None and user_descriptor[1] != '' and user_descriptor[1] != '##null##':
                    email = user_descriptor[1]

                if user_descriptor[2] is not None and user_descriptor[2] != '' and user_descriptor[2] != '##null##':
                    country = user_descriptor[2]

                if user_descriptor[3] is not None and user_descriptor[3] != '' and user_descriptor[3] != '##null##':
                    custom = {'Custom1': user_descriptor[3]}

                user_object = User(identifier, email, country, custom)

            i = 0
            for setting_key in setting_keys:
                print('------------------------------')
                value = client.get_value(setting_key, None, user_object)
                if str(value) != str(user_descriptor[i + 4]):
                    errors += 'Identifier: ' + user_descriptor[0] + '. SettingKey: ' + setting_key + \
                              '. Expected: ' + str(user_descriptor[i + 4]) + '. Result: ' + str(value) + '.\n'
                i += 1

        self.assertEqual('', errors)
        client.stop()

    def test_wrong_user_object(self):
        client = configcatclient.create_client('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
        setting_value = client.get_value('stringContainsDogDefaultCat', 'Lion', {'Email': 'a@configcat.com'})
        self.assertEqual('Cat', setting_value)
        client.stop()


'''
    def test_create_matrix_text(self):
        self._test_create_matrix('./testmatrix.csv', './testmatrix_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
    
    def test_create_matrix_semantic(self):
        self._test_create_matrix('./testmatrix_semantic.csv', './testmatrix_semantic_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/BAr3KgLTP0ObzKnBTo5nhA')
    
    def test_create_matrix_number(self):
        self._test_create_matrix('./testmatrix_number.csv', './testmatrix_number_out.csv',
                                 'PKDVCLf-Hq-h-kCzMp-L7Q/uGyK3q9_ckmdxRyI7vjwCw')
    
    def _test_create_matrix(self, file_path, out_file_path, api_key):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, file_path)
        out_file_path = path.join(script_dir, out_file_path)

        with open(file_path, 'r') as f:
            content = f.readlines()

        # CSV header
        header = content[0].rstrip()
        setting_keys = header.split(';')[4:]
        content.pop(0)

        client = configcatclient.create_client(api_key)
        with open(out_file_path, 'w') as f:
            f.writelines(header + '\n')

            for line in content:
                user_descriptor = line.rstrip().split(';')[:4]
                user_object = None
                if user_descriptor[0] is not None and user_descriptor[0] != '' and user_descriptor[0] != '##null##':
                    identifier = user_descriptor[0]
                     
                    email = None
                    if user_descriptor[1] is not None and user_descriptor[1] != '' and user_descriptor[1] != '##null##':
                        email = user_descriptor[1]
                        
                    country = None
                    if user_descriptor[2] is not None and user_descriptor[2] != '' and user_descriptor[2] != '##null##':
                        country = user_descriptor[2]
                        
                    custom = None
                    if user_descriptor[3] is not None and user_descriptor[3] != '' and user_descriptor[3] != '##null##':
                        custom = {'Custom1': user_descriptor[3]}
                    
                    user_object = User(identifier, email, country, custom)

                for setting_key in setting_keys:
                    value = client.get_value(setting_key, None, user_object)
                    user_descriptor.append(str(value))

                f.writelines(';'.join(user_descriptor)  + '\n')
'''