"""
You should install the ConfigCat-Client package before using this sample project
pip install configcat-client
"""

import configcatclient
import logging
from configcatclient.user import User

# Info level logging helps to inspect the feature flag evaluation process.
# Use the default warning level to avoid too detailed logging in your application.
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    # Initialize the ConfigCatClient with an SDK Key.
    client = configcatclient.create_client(
        'PKDVCLf-Hq-h-kCzMp-L7Q/HhOWfwVtZ0mb30i9wi17GQ')

    # Creating a user object to identify your user (optional).
    userObject = User('Some UserID', email='configcat@example.com', custom={
                      'version': '1.0.0'})

    value = client.get_value(
        'isPOCFeatureEnabled', False, userObject)
    print("'isPOCFeatureEnabled' value from ConfigCat: " + str(value))

    client.close()
