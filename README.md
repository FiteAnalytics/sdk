---
title: APIs
tags: technology, documentation
---

# Fite Analytics Software Development Kit (SDK)

Fite Analytics offers a free and public REST API & WebSocket endpoint with a complementary SDK to demo our services.
Our API currently utilizes API keys for authentication.

## Introduction

This document details how to use the SDK to interact with Fite Analytics' services. Please refer to this document as the definitive
source of information.

For questions or comments please contact us [via email](mailto:info@fiteanalytics.com) or on [reddit](https://www.reddit.com/r/fiteanalytics/).

## FinX API SDK
The FinX API consists of a RESTful API and a WebSocket endpoint offering rich fixed income analytics calculations, 
including security reference data, interest rate risk metrics, and projected cash flows. The Fite Analytics SDK offers
class-based client implementation for a variety of programming languages to wrap access to the API methods.

The FinX API requires an API key for usage - contact us to obtain your key: <info@fiteanalytics.com>. We require at 
minimum an API key for authentication. You may also be provided with a specific URL for accessing services - if you do
do not specify one, the URL will be set to https://sandbox.finx.io/api/. 

The SDK facilitates two distinct methods for securely passing credentials to the API clients.

The first method looks for the required credentials in environment variables. The following should be set before running.
### Environment Variables
```
export FINX_API_KEY=my_api_key
export FINX_API_ENDPOINT=my_api_endpoint
```

The second method is by manually passing kwargs into the client constructor. We do NOT recommend hard-coding your 
credentials in your code.
### Keyword Arguments - handle with care!
```python
:keyword finx_api_key: (string)
:keyword finx_api_endpoint: (string)
```

### SDK Installation

The SDK can be installed via pip for versions >= 2.0.0
```shell script
pip3 install fiteanalytics==2.0.0
```

### Quickstart

The following is an example of how to import and use the SDK.

#### Python
```python
import json
from fiteanalytics import finx_api

# Initialize synchronous client with no arguments - 
# checks environment variables for credentials
finx = finx_api.FinX()

# Get API methods
print('\n*********** API Methods ***********')
api_methods = finx.get_api_methods()
print(json.dumps(api_methods, indent=4))

security_id = 'USQ98418AH10'
as_of_date = '2020-09-14'

# Get security reference data
print('\n*********** Security Reference Data ***********')
reference_data = finx.get_security_reference_data(
    security_id, 
    as_of_date=as_of_date)
print(json.dumps(reference_data, indent=4))

# Get security analytics
print('\n*********** Security Analytics ***********')
analytics = finx.get_security_analytics(
    security_id, 
    as_of_date=as_of_date, 
    price=100)
print(json.dumps(analytics, indent=4))

# Get projected cash flows
print('\n*********** Security Cash Flows ***********')
cash_flows = finx.get_security_cash_flows(
    security_id, 
    as_of_date=as_of_date, 
    price=100)
print(json.dumps(cash_flows, indent=4))
```

## Python SDK
### Client Types
The SDK offers three distinct client types for using the FinX API. Each of these clients employs a highly performant 
Least-Recently-Used (LRU) cache under the hood. You can specify the maximum cache size using the ```max_cache_size``` 
keyword argument in the constructor - the default is ```100```.

When invoking a function, the client will construct a cache key from the name of the function being called and the 
parameters being passed. The client then uses this key to check if a response has already been recorded in the cache, 
and returns the response if so. Otherwise, it dispatches the request to the FinX API and records the response in the 
cache once it is received. The cache may be cleared using 
```python
finx.clear_cache()
```
This feature is especially important for the WebSocket client, since responses are received and parsed asynchronously 
using callback functions. Retrieving results relies on this functionality.

#### Synchronous HTTP Client
Makes blocking synchronous requests in each function. 
##### Initialization
```python
finx = finx_api.FinX()
```

#### Asynchronous HTTP Client
Capable of dispatching multiple requests concurrently using asyncio.
##### Initialization
```python
finx = finx_api.FinX('async')
``` 
All functions are asynchronous and must therefore be awaited.

#### WebSocket Client
WebSocket client which runs a WebSocket connection in a separate thread, capable of dispatching multiple requests 
concurrently.
##### Initialization
```python
finx = finx_api.FinX('socket')
```
By their nature, WebSockets are asynchronous. Function calls using this client therefore will generally not return 
the API response unless the request has been cached. If the request has not been cached, the function will return the 
cache key that will be used to store the response in the cache when it is received.

For all of the WebSocket client's methods, the ```callback``` keyword argument may be used to define a function to be 
executed on the response when it is received, regardless of whether or not it was found in the cache. The function 
should take the response object as a parameter and optional keyword arguments specified in the original function call. 
Note that the callback will not block the main thread. Here is an example of its usage:
```python
def my_callback(response, **kwargs):
    print(f'\nCallback got the response: {response}\n')
    print(f'Keyword arguments: {kwargs}')


finx = finx_api.FinX('socket')
finx.get_api_methods(callback=my_callback, my_callback_kwarg='foo')
```
If you prefer not to use the callback functionality or would like to wait for the response before proceeding in your 
program, you can always use the returned cache key to interact with the cache directly:
```python
finx = finx_api.FinX('socket')
response = finx.get_api_methods()
if type(response) is str:
    cache_key = response
    response = None
    while response is None:
        response = finx.cache.get(cache_key)
print(response)
``` 

#### Get API Methods

```
Inputs: 
    :keyword callback: websocket client only

Output: A object mapping each available API method to their respective required and optional parameters
```
##### Example
```python
api_methods = finx.get_api_methods()
print(json.dumps(api_methods, indent=4))                      
```
###### Output
```json5
{
    "hello_world": {
        "required": [
            "my_name"
        ],
        "optional": [
            "my_favorite_animal"
        ]
    },
    "security_reference": {
        "required": [
            "security_id"
        ],
        "optional": [
            "as_of_date"
        ]
    },
    "security_analytics": {
        "required": [
            "security_id"
        ],
        "optional": [
            "price",
            "as_of_date",
            "volatility",
            "yield_shift",
            "shock_in_bp",
            "horizon_months",
            "income_tax",
            "cap_gain_short_tax",
            "cap_gain_long_tax",
            "use_kalotay_analytics"
        ]
    },
    "security_cash_flows": {
        "required": [
            "security_id"
        ],
        "optional": [
            "as_of_date",
            "price",
            "shock_in_bp"
        ]
    },
    "list_api_functions": {
        "required": [],
        "optional": []
    },
}

```


#### Get Security Reference Data


```
Inputs:
    :param security_id: string
    :keyword as_of_date: string as YYYY-MM-DD (optional)
    :keyword callback: websocket client only

Output: An object containing various descriptive fields for the specified security
```
##### Example
```python
reference_data = finx.get_security_reference_data(
    '655664AP5', 
    as_of_date='2017-12-19')
print(json.dumps(reference_data, indent=4))
```
###### Output
```json5
{
    "security_id": "655664AP5",
    "as_of_date": "2017-12-19",
    "security_name": null,
    "asset_class": "bond",
    "security_type": "corporate",
    "government_type": null,
    "corporate_type": null,
    "municipal_type": null,
    "structured_type": null,
    "mbspool_type": null,
    "currency": "USD",
    "first_coupon_date": "2012-04-15T00:00:00Z",
    "maturity_date": "2021-10-15T00:00:00Z",
    "issue_date": "2011-10-11T00:00:00Z",
    "issuer_name": "Nordstrom, Inc.",
    "price": null,
    "accrued_interest": 0.7111111111111111,
    "current_coupon": 4.0,
    "has_optionality": true,
    "has_sinking_schedule": false,
    "has_floating_rate": false
}
```

#### Get Security Analytics

```
Inputs:
    :param security_id: string
    :keyword as_of_date: string as YYYY-MM-DD (optional)
    :keyword price: float (optional)
    :keyword volatility: float (optional)
    :keyword yield_shift: int (basis points, optional)
    :keyword shock_in_bp: int (basis points, optional)
    :keyword horizon_months: uint (optional)
    :keyword income_tax: float (optional)
    :keyword cap_gain_short_tax: float (optional)
    :keyword cap_gain_long_tax: float (optional)
    :keyword callback: websocket client only

Output: An object containing various fixed income risk analytics measures for the specified security and parameters
```

##### Example
```python
analytics = finx.get_security_analytics(
    '655664AP5', 
    as_of_date='2017-12-19', 
    price=102.781)
print(json.dumps(analytics, indent=4))
```
###### Output
```json5
{
    "security_id": "655664AP5",
    "as_of_date": "2017-12-19T00:00:00Z",
    "price": 102.781,
    "convexity_par": -1.4169,
    "dur_to_worst": 3.241,
    "dur_to_worst_ann": 3.4508,
    "eff_dur_par": 3.3744,
    "eff_dur_spot": 3.3744,
    "local_dur": 3.4508,
    "macaulay_dur": 3.5628,
    "macaulay_dur_to_worst": 3.2924,
    "modified_dur": 3.5063,
    "modified_dur_ann": 3.4508,
    "libor_oas": 0.0099,
    "oas": 0.0113,
    "yield_to_maturity_ann": 0.0325,
    "yield_to_option": 0.0317,
    "yield_value_32": 0.0001,
    "spread_dur": 3.2951,
    "accrued_interest": 0.7111111111111111,
    "asset_swap_spread": 0.0102,
    "average_life": 3.5722222222222224,
    "coupon_rate": 4.0,
    "current_yield": 0.0389,
    "discount_margin": -9999,
    "convexity_spot": -1.4178,
    "dv01": 0.0363,
    "maturity_years": 3.8222,
    "nominal_spread": 0.0114,
    "stated_maturity_years": 3.8222,
    "yield_to_maturity": 0.0322,
    "yield_to_put": 0.0322,
    "annual_yield": 0.0404,
    "zvo": 0.0113
}
```

#### Get Security Cash Flows

```
Inputs:
    :param security_id: string
    :keyword as_of_date: string as YYYY-MM-DD (optional)
    :keyword price: float (optional)
    :keyword shock_in_bp: int (optional)
    :keyword callback: websocket client only

Output: An object containing a vector time series of cash flow dates and corresponding amounts
```

##### Example
```python
cash_flows = finx.get_security_cash_flows(
    '655664AP5', 
    as_of_date='2017-12-19', 
    price=102.781)
print(json.dumps(cash_flows, indent=4))
```
###### Output
```json5
{
    "security_id": "655664AP5",
    "as_of_date": "2017-12-19",
    "cash_flows": [
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2018-04-15"
        },
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2018-10-15"
        },
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2019-04-15"
        },
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2019-10-15"
        },
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2020-04-15"
        },
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2020-10-15"
        },
        {
            "total_cash_flows": 2.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 0.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2021-04-15"
        },
        {
            "total_cash_flows": 0.0,
            "interest_cash_flows": 0.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 100.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 1.0,
            "cash_flow_date": "2021-07-15"
        },
        {
            "total_cash_flows": 0.0,
            "interest_cash_flows": 0.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 100.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 1.3333333333333333,
            "cash_flow_date": "2021-08-15"
        },
        {
            "total_cash_flows": 0.0,
            "interest_cash_flows": 0.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 0.0,
            "call_cash_flows": 100.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 1.6666666666666667,
            "cash_flow_date": "2021-09-15"
        },
        {
            "total_cash_flows": 102.0,
            "interest_cash_flows": 2.0,
            "other_principal_cash_flows": 0.0,
            "principal_cash_flows": 100.0,
            "call_cash_flows": 100.0,
            "put_cash_flows": 0.0,
            "accrued_interest": 0.0,
            "cash_flow_date": "2021-10-15"
        }
    ]
}
```

#### Batch

```
Inputs:
    :param function: Client member function to invoke for each security
    :param security_args: Object mapping security_id (string) to an object of key word arguments for the function 
    :keyword callback: websocket client only    

Output: A list of corresponding results for each security ID specified
```

##### Example
```python
reference_data = finx.batch(
    finx_client.get_security_reference_data, 
    {
        'USQ98418AH10': {
            'as_of_date': '2020-09-14'
        }, 
        '3133XXP50': {
            'as_of_date': '2020-09-14'
        }   
    })
print(json.dumps(reference_data, indent=4))
```
###### Output
```json5
[
    {
        "security_id": "USQ98418AH10",
        "as_of_date": "2021-03-09",
        "security_name": null,
        "asset_class": "bond",
        "security_type": "corporate",
        "government_type": null,
        "corporate_type": null,
        "municipal_type": null,
        "structured_type": null,
        "mbspool_type": null,
        "currency": "USD",
        "maturity_date": "2020-09-22T00:00:00Z",
        "issue_date": "2010-09-22T00:00:00Z",
        "issuer_name": "Woolworths Group Limited",
        "current_coupon": 4.0,
        "has_optionality": false,
        "has_sinking_schedule": false,
        "has_floating_rate": false
    },
    {
        "security_id": "3133XXP50",
        "as_of_date": "2021-03-09",
        "security_name": null,
        "asset_class": "bond",
        "security_type": "government",
        "government_type": null,
        "corporate_type": null,
        "municipal_type": null,
        "structured_type": null,
        "mbspool_type": null,
        "currency": "USD",
        "maturity_date": "2020-03-13T00:00:00Z",
        "issue_date": "2010-03-16T00:00:00Z",
        "issuer_name": "Federal Home Loan Banks",
        "current_coupon": 4.125,
        "has_optionality": false,
        "has_sinking_schedule": false,
        "has_floating_rate": false
    }
]
```

### Javascript SDK

The Javascript SDK is similarly implemented as a wrapper class with member functions for invoking the various API 
methods, however, all methods are implemented as asynchronous functions and must be invoked accordingly. Key word arguments 
must be specified using a map object argument for the initialization, security analytics and security cash flows 
functions since key words are not natively supported by javascript.

Ensure you have installed the packages listed in package.json:
```shell script
cd ~/sdk/node
npm install
```

#### Initialization

##### Inputs

1. YAML configuration file formatted as described above (optional)
2. .env file formatted as described above (optional)

##### Output

Returns a class object with member functions for invoking the various API methods

##### Example
```js
import FinX from "finx_api/finx.js";

// Checks environment variables;
let finx = FinX();
```

#### Get API Methods

##### Inputs

None

##### Output

A object mapping each available API method to their respective required and optional parameters

##### Example
```js
finx.get_api_methods().then(data => console.log(data));
```
###### Output
```json5
{
  hello_world: { required: [ 'my_name' ], optional: [ 'my_favorite_animal' ] },
  security_reference: { required: [ 'security_id' ], optional: [ 'as_of_date' ] },
  security_analytics: {
    required: [ 'security_id' ],
    optional: [
      'price',
      'as_of_date',
      'volatility',
      'yield_shift',
      'shock_in_bp',
      'horizon_months',
      'income_tax',
      'cap_gain_short_tax',
      'cap_gain_long_tax',
      'use_kalotay_analytics'
    ]
  },
  security_cash_flows: {
    required: [ 'security_id' ],
    optional: [ 'as_of_date', 'price', 'shock_in_bp' ]
  },
  list_api_functions: { required: [], optional: [] },
}
```


#### Get Security Reference Data

##### Inputs

```
:param security_id: string
:param as_of_date: string as YYYY-MM-DD (optional)
```

##### Output

An object containing various descriptive fields for the specified security

##### Example
```js
finx.get_security_reference_data(
    'USQ98418AH10', 
    '2020-09-14'
).then(data => console.log(data));
```
###### Output
```json5
{
  security_id: 'USQ98418AH10',
  as_of_date: '2020-09-14',
  security_name: null,
  asset_class: 'bond',
  security_type: 'corporate',
  government_type: null,
  corporate_type: null,
  municipal_type: null,
  structured_type: null,
  mbspool_type: null,
  currency: 'USD',
  maturity_date: '2020-09-22T00:00:00Z',
  issue_date: '2010-09-22T00:00:00Z',
  issuer_name: 'Woolworths Group Limited',
  current_coupon: 4,
  has_optionality: false,
  has_sinking_schedule: false,
  has_floating_rate: false
}
```

#### Get Security Analytics

##### Inputs

```
:param security_id: string
:keyword as_of_date: string as YYYY-MM-DD (optional)
:keyword price: float (optional)
:keyword volatility: float (optional)
:keyword yield_shift: int (basis points, optional)
:keyword shock_in_bp: int (basis points, optional)
:keyword horizon_months: uint (optional)
:keyword income_tax: float (optional)
:keyword cap_gain_short_tax: float (optional)
:keyword cap_gain_long_tax: float (optional)
```

##### Output

An object containing various fixed income risk analytics measures for the specified security and parameters

##### Example
```js
finx.get_security_analytics(
    'USQ98418AH10', 
    {
        as_of_date: '2020-09-14', 
        price: 100
    }
).then(data => console.log(data));
```
###### Output
```json5
{
  security_id: 'USQ98418AH10',
  as_of_date: '2020-09-14T00:00:00Z',
  price: 100,
  convexity_par: 0.0002,
  dur_to_worst: 0.0218,
  dur_to_worst_ann: 0.0214,
  eff_dur_par: 0.0222,
  eff_dur_spot: 0.0222,
  local_dur: 0.0214,
  macaulay_dur: 0.0222,
  macaulay_dur_to_worst: 0.0222,
  modified_dur: 0.0218,
  modified_dur_ann: 0.0214,
  libor_oas: 0.0369,
  oas: 0.0382,
  yield_to_maturity_ann: 0.04,
  yield_to_option: 0.0396,
  yield_value_32: 0.014,
  spread_dur: 0.0222,
  accrued_interest: 1.9111,
  asset_swap_spread: 0.0373,
  average_life: 0.022222222222222195,
  coupon_rate: 4,
  current_yield: 0.04,
  discount_margin: -9999,
  convexity_spot: 0.0002,
  dv01: 0.0002,
  maturity_years: 0.0222,
  nominal_spread: 0.0386,
  stated_maturity_years: 0.0222,
  yield_to_maturity: 0.0396,
  yield_to_put: 0.0396,
  annual_yield: 0.0404,
  zvo: 0.0382
}
```

#### Get Security Cash Flows

##### Inputs

```
:param security_id: string
:keyword as_of_date: string as YYYY-MM-DD (optional)
:keyword price: float (optional)
:keyword shock_in_bp: int (optional)
```

##### Output

An object containing a vector time series of cash flow dates and corresponding amounts

##### Example
```js
finx.get_security_cash_flows(
    'USQ98418AH10', 
    {
        as_of_date: '2020-09-14', 
        price: 100
    }
).then(data => console.log(data));
```
###### Output
```json5
{
  security_id: 'USQ98418AH10',
  as_of_date: '2020-09-14',
  cash_flows: [
    {
      total_cash_flows: 102,
      interest_cash_flows: 2,
      other_principal_cash_flows: 0,
      principal_cash_flows: 100,
      call_cash_flows: 0,
      put_cash_flows: 0,
      accrued_interest: 0,
      cash_flow_date: '2020-09-22'
    }
  ]
}
```

#### Batch

##### Inputs

```
:param function: Client member function to invoke for each security
:param security_args: Object mapping security_id (string) to an object of key word arguments 
```

##### Output

A list of corresponding results for each security ID specified

##### Example
```javascript
reference_data = finx.batch(
    finx.get_security_reference_data, 
    {
        USQ98418AH10: {
            as_of_date: '2020-09-14'
        }, 
        3133XXP50: {
            as_of_date: '2020-09-14'
        }   
    }
).then(data => console.log(data));
```

##### Output
```json5
[
  {
    security_id: 'USQ98418AH10',
    as_of_date: '2020-09-14',
    security_name: null,
    asset_class: 'bond',
    security_type: 'corporate',
    government_type: null,
    corporate_type: null,
    municipal_type: null,
    structured_type: null,
    mbspool_type: null,
    currency: 'USD',
    first_coupon_date: '2011-03-22T00:00:00Z',
    maturity_date: '2020-09-22T00:00:00Z',
    issue_date: '2010-09-22T00:00:00Z',
    issuer_name: 'Woolworths Group Limited',
    price: null,
    accrued_interest: 1.9111111111111112,
    current_coupon: 4,
    has_optionality: false,
    has_sinking_schedule: false,
    has_floating_rate: false
  },
  {
    security_id: '3133XXP50',
    as_of_date: '2020-09-14',
    security_name: null,
    asset_class: 'bond',
    security_type: 'government',
    government_type: null,
    corporate_type: null,
    municipal_type: null,
    structured_type: null,
    mbspool_type: null,
    currency: 'USD',
    first_coupon_date: '2010-09-13T00:00:00Z',
    maturity_date: '2020-03-13T00:00:00Z',
    issue_date: '2010-03-16T00:00:00Z',
    issuer_name: 'Federal Home Loan Banks',
    price: null,
    accrued_interest: 2.073958333333333,
    current_coupon: 4.125,
    has_optionality: false,
    has_sinking_schedule: false,
    has_floating_rate: false
  }
]
```
