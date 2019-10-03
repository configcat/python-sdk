"""
You should install the ConfigCat-Client package before using this sample project
pip install configcat-client
"""

import configcatclient
from configcatclient.user import User

if __name__ == '__main__':
    # Initialize the ConfigCatClient with an API Key.
    client = configcatclient.create_client('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')

    # In the project there is a 'keySampleText' setting with the following rules:
    # 1. If the User's country is Hungary, the value should be 'Dog'
    # 2. If the User's custom property - SubscriptionType - is unlimited, the value should be 'Lion'
    # 3. In other cases there is a percentage rollout configured with 50% 'Falcon' and 50% 'Horse' rules.
    # 4. There is also a default value configured: 'Cat'

    # 1. As the passed User's country is Hungary this will print 'Dog'
    my_setting_value = client.get_value('keySampleText', 'default value', User('key', country='Hungary'))
    print("'keySampleText' value from ConfigCat: " + str(my_setting_value))

    # 2. As the passed User's custom attribute - SubscriptionType - is unlimited this will print 'Lion'
    my_setting_value = client.get_value('keySampleText', 'default value',
                                        User('key', custom={'SubscriptionType': 'unlimited'}))
    print("'keySampleText' value from ConfigCat: " + str(my_setting_value))

    # 3/a. As the passed User doesn't fill in any rules, this will serve 'Falcon' or 'Horse'.
    my_setting_value = client.get_value('keySampleText', 'default value', User('key'))
    print("'keySampleText' value from ConfigCat: " + str(my_setting_value))

    # 3/b. As this is the same user from 3/a., this will print the same value as the previous one ('Falcon' or 'Horse')
    my_setting_value = client.get_value('keySampleText', 'default value', User('key'))
    print("'keySampleText' value from ConfigCat: " + str(my_setting_value))

    # 4. As we don't pass an User object to this call, this will print the setting's default value - 'Cat'
    my_setting_value = client.get_value('keySampleText', 'default value')
    print("'keySampleText' value from ConfigCat: " + str(my_setting_value))

    # 'myKeyNotExits' setting doesn't exist in the project configuration and the client returns default value ('N/A');
    my_setting_not_exists = client.get_value('myKeyNotExists', 'N/A')
    print("'myKeyNotExists' value from ConfigCat: " + str(my_setting_not_exists))

    client.stop()
