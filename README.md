# ConfigCat SDK for Python
ConfigCat SDK for Python provides easy integration between ConfigCat service and applications using Python.

ConfigCat is a feature flag, feature toggle, and configuration management service. That lets you launch new features and change your software configuration remotely without actually (re)deploying code. ConfigCat even helps you do controlled roll-outs like canary releases and blue-green deployments.
https://configcat.com  

[![Build Status](https://travis-ci.com/configcat/python-sdk.svg?branch=master)](https://travis-ci.com/configcat/python-sdk) 
[![codecov](https://codecov.io/gh/ConfigCat/python-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/ConfigCat/python-sdk)
[![PyPI](https://img.shields.io/pypi/v/configcat-client.svg)](https://pypi.python.org/pypi/configcat-client)
[![PyPI](https://img.shields.io/pypi/pyversions/configcat-client.svg)](https://pypi.python.org/pypi/configcat-client)
[![Known Vulnerabilities](https://snyk.io/test/github/configcat/python-sdk/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/configcat/python-sdk?targetFile=requirements.txt)
![License](https://img.shields.io/github/license/configcat/python-sdk.svg)

## Getting started

### 1. Install the package with `pip`

```bash
pip install configcat-client
```

### 2. Import `configcatclient` to your application

```python
import configcatclient
```

### 3. <a href="https://configcat.com/Account/Login" target="_blank">Log in to ConfigCat Management Console</a> and go to your *Project* to get your *API Key*:
![API-KEY](https://raw.githubusercontent.com/ConfigCat/python-sdk/master/media/readme01.png  "API-KEY")

### 4. Create a *ConfigCat* client instance:

```python
configcat_client = configcatclient.create_client('#YOUR-API-KEY#')
```
> We strongly recommend using the *ConfigCat Client* as a Singleton object in your application.

### 5. Get your setting value
```python
isMyAwesomeFeatureEnabled = configcat_client.get_value('isMyAwesomeFeatureEnabled', False)
if isMyAwesomeFeatureEnabled:
    do_the_new_thing()
else:
    do_the_old_thing()
```

### 6. Stop *ConfigCat* client on application exit
```python
configcat_client.stop()
```

## Getting user specific setting values with Targeting
Using this feature, you will be able to get different setting values for different users in your application by passing a `User Object` to the `get_value()` function.

Read more about [Targeting here](https://docs.configcat.com/docs/advanced/targeting/).
```python
from configcatclient.user import User 

user = User('#USER-IDENTIFIER#')

isMyAwesomeFeatureEnabled = configcat_client.get_value('isMyAwesomeFeatureEnabled', False, user)
if isMyAwesomeFeatureEnabled:
    do_the_new_thing()
else:
    do_the_old_thing()
```

## Sample/Demo apps
* [Sample Console App](https://github.com/configcat/python-sdk/tree/master/samples/consolesample)
* [Sample Django Web App](https://github.com/configcat/python-sdk/tree/master/samples/webappsample)

## Polling Modes
The ConfigCat SDK supports 3 different polling mechanisms to acquire the setting values from ConfigCat. After latest setting values are downloaded, they are stored in the internal cache then all requests are served from there. Read more about Polling Modes and how to use them at [ConfigCat Docs](https://docs.configcat.com/docs/sdk-reference/python/).

## Support
If you need help how to use this SDK feel free to to contact the ConfigCat Staff on https://configcat.com. We're happy to help.

## Contributing
Contributions are welcome.

## About ConfigCat
- [Documentation](https://docs.configcat.com)
- [Blog](https://blog.configcat.com)