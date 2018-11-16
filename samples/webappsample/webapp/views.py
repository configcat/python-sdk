from django.http import HttpResponse
from configcatclient.user import User
from webapp.apps import WebappConfig

# In the project there is a 'keySampleText' setting with the following rules:
# 1. If the User's country is Hungary, the value should be 'Dog'
# 2. If the User's custom property - SubscriptionType - is unlimited, the value should be 'Lion'
# 3. In other cases there is a percentage rollout configured with 50% 'Falcon' and 50% 'Horse' rules.
# 4. There is also a default value configured: 'Cat'


# 1. As the passed User's country is Hungary this will return 'Dog'.
def index1(request):
    my_setting_value = WebappConfig.configcat_client.get_value('keySampleText', 'default value',
                                                              User('key', country='Hungary'))
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(my_setting_value))


# 2. As the passed User's custom attribute - SubscriptionType - is unlimited this will return 'Lion'.
def index2(request):
    my_setting_value = WebappConfig.configcat_client.get_value('keySampleText', 'default value',
                                                              User('key', custom={'SubscriptionType': 'unlimited'}))
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(my_setting_value))


# 3/a. As the passed User doesn't fill in any rules, this will return 'Falcon' or 'Horse'.
def index3a(request):
    my_setting_value = WebappConfig.configcat_client.get_value('keySampleText', 'default value', User('key'))
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(my_setting_value))


# 3/b. As this is the same user from 3/a., this will return the same value as the previous one ('Falcon' or 'Horse').
def index3b(request):
    my_setting_value = WebappConfig.configcat_client.get_value('keySampleText', 'default value', User('key'))
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(my_setting_value))


# 4. As we don't pass an User object to this call, this will return the setting's default value - 'Cat'.
def index4(request):
    my_setting_value = WebappConfig.configcat_client.get_value('keySampleText', 'default value')
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(my_setting_value))


# 'myKeyNotExits' setting doesn't exist in the project configuration and the client returns default value ('N/A');
def index5(request):
    my_setting_value = WebappConfig.configcat_client.get_value('myKeyNotExits', 'N/A')
    return HttpResponse("Hello, world. 'keySampleText' value from ConfigCat: " + str(my_setting_value))
