# ConfigCat SDK for Python
https://configcat.com  
ConfigCat SDK for Python provides easy integration for your application to ConfigCat.

ConfigCat is a feature flag and configuration management service that lets you separate releases from deployments. You can turn your features ON/OFF using <a href="http://app.configcat.com" target="_blank">ConfigCat Dashboard</a> even after they are deployed. ConfigCat lets you target specific groups of users based on region, email or any other custom user attribute.

ConfigCat is a <a href="https://configcat.com" target="_blank">hosted feature flag service</a>. Manage feature toggles across frontend, backend, mobile, desktop apps. <a href="https://configcat.com" target="_blank">Alternative to LaunchDarkly</a>. Management app + feature flag SDKs.

[![Python CI](https://github.com/configcat/python-sdk/actions/workflows/python-ci.yml/badge.svg?branch=master)](https://github.com/configcat/python-sdk/actions/workflows/python-ci.yml) 
[![codecov](https://codecov.io/gh/ConfigCat/python-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/ConfigCat/python-sdk)
[![PyPI](https://img.shields.io/pypi/v/configcat-client.svg)](https://pypi.python.org/pypi/configcat-client)
[![PyPI](https://img.shields.io/pypi/pyversions/configcat-client.svg)](https://pypi.python.org/pypi/configcat-client)
[![Known Vulnerabilities](https://snyk.io/test/github/configcat/python-sdk/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/configcat/python-sdk?targetFile=requirements.txt)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=configcat_python-sdk&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=configcat_python-sdk)
![License](https://img.shields.io/github/license/configcat/python-sdk.svg)

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-orange.svg)](https://sonarcloud.io/dashboard?id=configcat_python-sdk)

## Getting started

### 1. Install the package with `pip`

```bash
pip install configcat-client
```

### 2. Import `configcatclient` to your application

```python
import configcatclient
```

### 3. Go to the <a href="https://app.configcat.com/sdkkey" target="_blank">ConfigCat Dashboard</a> to get your *SDK Key*:
![SDK-KEY](https://raw.githubusercontent.com/ConfigCat/python-sdk/master/media/readme02-3.png  "SDK-KEY")

### 4. Create a *ConfigCat* client instance:

```python
configcat_client = configcatclient.get('#YOUR-SDK-KEY#')
```

> We strongly recommend you to use the *ConfigCat Client* as a Singleton object in your application. The `configcatclient.get()` static factory method constructs singleton client instances for your SDK keys.

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
configcat_client.close()
```

## Getting user specific setting values with Targeting
Using this feature, you will be able to get different setting values for different users in your application by passing a `User Object` to the `get_value()` function.

Read more about [Targeting here](https://configcat.com/docs/advanced/targeting/).
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
The ConfigCat SDK supports 3 different polling mechanisms to acquire the setting values from ConfigCat. After latest setting values are downloaded, they are stored in the internal cache then all requests are served from there. Read more about Polling Modes and how to use them at [ConfigCat Docs](https://configcat.com/docs/sdk-reference/python/).

## Need help?
https://configcat.com/support

## Contributing
Contributions are welcome. For more info please read the [Contribution Guideline](CONTRIBUTING.md).

## About ConfigCat
- [Official ConfigCat SDKs for other platforms](https://github.com/configcat)
- [Documentation](https://configcat.com/docs)
- [Blog](https://configcat.com/blog)
