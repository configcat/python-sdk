# ConfigCat SDK for Python
ConfigCat is a cloud based configuration as a service. It integrates with your apps, backends, websites, and other programs, so you can configure them through this website even after they are deployed.
https://configcat.com  

[![Build Status](https://travis-ci.org/configcat/python-sdk.svg?branch=master)](https://travis-ci.org/configcat/python-sdk) 
[![codecov](https://codecov.io/gh/ConfigCat/python-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/ConfigCat/python-sdk)
[![PyPI](https://img.shields.io/pypi/v/configcat-client.svg)](https://pypi.python.org/pypi/configcat-client)
[![PyPI](https://img.shields.io/pypi/pyversions/configcat-client.svg)](https://pypi.python.org/pypi/configcat-client)

## Getting started

**1. Install the ConfigCat-Client package with `pip`**

```bash
pip install configcat-client
```

**2. Import `configcatclient` to your application**

```python
import configcatclient

# Optional import
from configcatclient.user import User 
```

**3. Get your API Key from the [ConfigCat.com](https://configcat.com) portal**

![YourConnectionUrl](https://raw.githubusercontent.com/configcat/python-sdk/master/media/readme01.png  "ApiKey")

**4. Initialize the client**

```python
configcatclient.initialize('<PLACE-YOUR-API-KEY-HERE>')
```

**5. Get your config value**
```python
# optional User object initialization for rollout calculations. 
user = User('<EMAIL_OR_SESSIONID_OR_USERID>')

isMyAwesomeFeatureEnabled = configcatclient.get_value('key-of-my-awesome-feature', False, user)
if isMyAwesomeFeatureEnabled:
    # show your awesome feature to the world!
```

**6. On application exit:**
```python
configcatclient.stop()
```

## User object
If you want to get advantage from our percentage rollout and targeted rollout features, you should pass a ```User``` object to the ```get_value(key, default_value, user)``` calls.
We strongly recommend you to pass the ```User``` object in every call so later you can use these awesome features without rebuilding your application.

```User(...)```

| ParameterName        | Description           | Default  |
| --- | --- | --- |
| ```key```      | Mandatory, unique identifier for the User or Session. e.g. Email address, Primary key, Session Id  | REQUIRED |
| ```email ```      | Optional parameter for easier targeting rule definitions |   None |
| ```country```      | Optional parameter for easier targeting rule definitions |   None | 
| ```custom```      | Optional dictionary for custom attributes of the User for advanced targeting rule definitions. e.g. User role, Subscription type. |   None |

Example simple user object:  
```python
User('developer@configcat.com')
```

Example user object with optional custom attributes:  
```python
User('developer@configcat.com', 'developer@configcat.com', 'Hungary', {'UserRole': 'admin', 'Subscription': 'unlimited'})
```


## Configuration
Client supports three different caching policies to acquire the configuration from ConfigCat. When the client fetches the latest configuration, puts it into the internal cache and serves any configuration acquisition from cache. With these caching policies you can manage your configurations' lifetimes easily.

### Auto polling (default)
Client downloads the latest configuration and puts into a cache repeatedly. Use ```poll_interval_seconds``` parameter to manage polling interval.
Use ```on_configuration_changed_callback``` parameter to get notification about configuration changes. 

### Lazy loading
Client downloads the latest configuration only when it is not present or expired in the cache. 
Use ```cache_time_to_live_seconds``` parameter to manage configuration lifetime.

### Manual polling
With this mode you always have to call ```force_refresh()``` method to fetch the latest configuration into the cache. When the cache is empty (for example after client initialization) and you try to acquire any value you'll get the default value!

---

Initializing the client and the configuration parameters are different for each cache policy:

### Auto polling  
```configcatclient.initialize(...)```

| ParameterName        | Description           | Default  |
| --- | --- | --- |
| ```api_key```      | API Key to access your configuration  | REQUIRED |
| ```poll_interval_seconds ```      | Polling interval|   60 | 
| ```max_init_wait_time_seconds```      | Maximum waiting time between the client initialization and the first config acquisition in secconds.|   5 |
| ```on_configuration_changed_callback```      | Callback to get notification about configuration changes. |   None |
| ```config_cache_class```      | Custom cache implementation class. |   None |

#### Example - increase ```poll_interval_seconds``` to 600 seconds:

```python
configcatclient.initialize('<PLACE-YOUR-API-KEY-HERE>', poll_interval_seconds=600)
```

#### Example - get notification about configuration changes via ```on_configuration_changed_callback```:  

```python
def configuration_changed_callback(self):
    # Configuration changed.
    pass
    
configcatclient.initialize('<PLACE-YOUR-API-KEY-HERE>', on_configuration_changed_callback=configuration_changed_callback)
```

### Lazy loading
```configcatclient.initialize_lazy_loading(...)```

| ParameterName        | Description           | Default  |
| --- | --- | --- | 
| ```api_key```      | API Key to access your configuration  | REQUIRED |
| ```cache_time_to_live_seconds```      | Use this value to manage the cache's TTL. |   60 |
| ```config_cache_class```      | Custom cache implementation class. |   None |

#### Example - increase ```cache_time_to_live_seconds``` to 600 seconds:

```python
configcatclient.initialize_lazy_loading('<PLACE-YOUR-API-KEY-HERE>', cache_time_to_live_seconds=600)
```

#### Example - use a custom ```config_cache_class```:

```python
from configcatclient.interfaces import ConfigCache


class InMemoryConfigCache(ConfigCache):

    def __init__(self):
        self._value = None

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

configcatclient.initialize_lazy_loading('<PLACE-YOUR-API-KEY-HERE>', config_cache_class=InMemoryConfigCache)
```

### Manual polling
```configcatclient.initialize_manual_polling(...)```

| ParameterName        | Description           | Default  |
| --- | --- | --- | 
| ```api_key```      | API Key to access your configuration  | REQUIRED |
| ```config_cache_class```      | Custom cache implementation class. |   None |

#### Example - call ```force_refresh()``` to fetch the latest configuration:

```python
configcatclient.initialize_manual_polling('<PLACE-YOUR-API-KEY-HERE>')
configcatclient.get_value('test_key', 'default_value') # This will return 'default_value' 
configcatclient.force_refresh()
configcatclient.get_value('test_key', 'default_value') # This will return the real value for key 'test_key'
```

## Members
### Methods
| Name        | Description           |
| :------- | :--- |
| ``` configcatclient.get_value(key, defaultValue, user=None) ``` | Returns the value of the key |
| ``` configcatclient.force_refresh() ``` | Fetches the latest configuration from the server. You can use this method with WebHooks to ensure up to date configuration values in your application. |

## Logging
The ConfigCat SDK uses the default Python `logging` package for logging.

## Sample projects
* [Console sample](https://github.com/configcat/python-sdk/tree/master/samples/consolesample)
* [Django web app sample](https://github.com/configcat/python-sdk/tree/master/samples/webappsample)