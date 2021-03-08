# Fite Analytics Software Development Kit (SDK)

## Introduction

This document details how to use the SDK to interact with Fite Analytics' services. Please refer to this document as the definitive
source of information.

For questions or comments please contact us [via email](mailto:info@fiteanalytics.com) or on [reddit](https://www.reddit.com/r/fiteanalytics/).

## FinX API SDK
The FinX API is a RESTful API endpoint offering rich fixed income analytics calculations, including security reference data, interest rate risk metrics, and projected cash flows. The Fite Analytics SDK offers a client class implementation for a variety of programming languages to wrap access to the API methods. Unless specified otherwise, each language's client implementation consist solely of one implementation file containing all the necessary code to expose the API functions.

The FinX API requires an API key for usage. You may also be provided with a specific URL for accessing services. Please contact us [via email](mailto:info@fiteanalytics.com) to obtain your key. We require three fields to validate your credentials: `VERSION`, `FINX_API_KEY` and `FINX_API_ENDPOINT`. Note that these keys are case sensitive. The SDK facilitates two distinct methods for securely passing credentials to the API clients.

The first method is via a YAML configuration file containing your credentials. You may give the path to this file when initializing the client:
#### YAML configuration syntax
```
VERSION: 1
FINX_API_KEY: my_finx_key
FINX_API_ENDPOINT: https://api.finx.io
```
The second method looks for the required credentials in environment variables. If a .env file is specified in the client initialization, the .env file will be loaded before checking the variables.
#### .env file syntax
```
VERSION=1
FINX_API_KEY=my_finx_key
FINX_API_ENDPOINT=https://api.finx.io
```

## SDK Installation

For the immediate future, please clone this repository into your project to begin using the SDK.
```
git clone https://github.com/FiteAnalytics/sdk
```

## Python SDK

The Python SDK is implemented as a wrapper class with member functions for invoking the various API methods.

#### Initialization

##### Inputs

1. YAML configuration file formatted as described above (optional)
2. .env file formatted as described above (optional)

##### Output

Returns a class object with member functions for invoking the various API methods

##### Example
```
from finx_api.finx import FinX

# YAML configuration file
finx = FinX(yaml_path='path/to/file.yml')

# .env file
finx = FinX(env_path='path/to/.env')

# No file (will check environment variables)
finx = FinX()
```

#### Get API Methods

##### Inputs

None

##### Output

An array of objects with descriptions of each available API method, including required and optional parameters

##### Example
```
>>> finx.get_api_methods()
>>> {'hello_world': {'required': ['my_name'], 'optional': ['my_favorite_animal']}, 'security_reference': {'required': ['security_id'], 'optional': ['as_of_date']}, 'security_analytics': {'required': ['security_id'], 'optional': ['price', 'as_of_date', 'volatility', 'yield_shift', 'shock_in_bp', 'horizon_months', 'income_tax', 'cap_gain_short_tax', 'cap_gain_long_tax', 'use_kalotay_analytics']}, 'security_cash_flows': {'required': ['security_id'], 'optional': ['as_of_date', 'price', 'shock_in_bp']}, 'get_account_info': {'required': ['finx_api_key', 'target_finx_api_key'], 'optional': ['as_of_date']}, 'list_api_keys': {'required': ['finx_api_key'], 'optional': ['as_of_date']}, 'list_api_functions': {'required': [], 'optional': []}, 'get_api_usage': {'required': ['finx_api_key'], 'optional': ['target_finx_api_key', 'as_of_date']}}
```


#### Security Reference

##### inputs

None

##### function syntax

fiteanalytics.hello_world()

###### example

```
> import fiteanalytics
>
> fiteanalytics.hello_world()
> 
> hello from fiteanalytics
```

#### security analytics

## Javascript SDK

We expect the Javascript SDK to be available in early Q2 2021.
