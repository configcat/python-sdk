import unittest
from os import path

import configcatclient
from configcatclient.user import User


class RolloutTests(unittest.TestCase):

    def test_matrix(self):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, './testmatrix.csv')

        with open(file_path, 'r') as f:
            content = f.readlines()

        # CSV header
        header = content[0].rstrip()
        setting_keys = header.split(';')[4:]
        content.pop(0)

        configcatclient.stop()
        configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
        errors = ''
        for line in content:
            test_object = line.rstrip().split(';')

            user_object = None
            if test_object[0] is not None and test_object[0] != '' and test_object[0] != '##nouserobject##':
                custom = None
                if test_object[3] is not None and test_object[3] != '':
                    custom = {'Custom1': test_object[3]}
                user_object = User(test_object[0], test_object[1], test_object[2], custom)

            i = 0
            for setting_key in setting_keys:
                value = configcatclient.get_value(setting_key, None, user_object)
                if str(value) != str(test_object[i + 4]):
                    value = configcatclient.get_value(setting_key, None, user_object)
                    errors += 'Key: ' + test_object[0] + '. SettingKey: ' + setting_key + \
                              '. Expected: ' + str(test_object[i + 4]) + '. Result: ' + str(value) + '.\n'
                i += 1

        self.assertEqual('', errors)

    """
    def test_create_matrix(self):
        script_dir = path.dirname(__file__)
        file_path = path.join(script_dir, './testmatrix.csv')
        out_file_path = path.join(script_dir, './testmatrix_out.csv')

        with open(file_path, 'r') as f:
            content = f.readlines()

        # CSV header
        header = content[0].rstrip()
        setting_keys = header.split(';')[4:]
        content.pop(0)

        configcatclient.stop()
        configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
        with open(out_file_path, 'w') as f:
            f.writelines(header + '\n')

            for line in content:
                user_descriptor = line.rstrip().split(';')[:4]
                user_object = None
                if user_descriptor[0] is not None and user_descriptor[0] != '' 
                    and user_descriptor[0] != '##nouserobject##':
                    custom = None
                    if user_descriptor[3] is not None and user_descriptor[3] != '':
                        custom = {'Custom1': user_descriptor[3]}
                    user_object = User(user_descriptor[0], user_descriptor[1], user_descriptor[2], custom)

                for setting_key in setting_keys:
                    value = configcatclient.get_value(setting_key, None, user_object)
                    user_descriptor.append(str(value))

                f.writelines(';'.join(user_descriptor)  + '\n')
    """