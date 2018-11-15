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

        client = configcatclient.create_client('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
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

        client = configcatclient.create_client('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
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
    """