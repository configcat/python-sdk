"""
You should install the ConfigCat-Client package before using this sample project
pip install configcat-client
"""

import configcatclient

if __name__ == '__main__':
    # Initialize the BetterConfigClient with a project secret.
    configcatclient.initialize('PKDVCLf-Hq-h-kCzMp-L7Q/PaDVCFk9EpmD6sLpGLltTA')

    # Current project's setting key name is 'keySampleText'
    my_setting_value = configcatclient.get().get_value('keySampleText', 'default value')
    print("'keySampleText' value from ConfigCat: " + str(my_setting_value))

    # 'myKeyNotExits' setting doesn't exist in the project configuration and the client returns default value ('N/A');
    my_setting_not_exists = configcatclient.get().get_value('myKeyNotExits', 'N/A')
    print("'myKeyNotExits' value from ConfigCat: " + str(my_setting_not_exists))

    configcatclient.stop()
