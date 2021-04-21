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
:keyword finx_api_key: string
:keyword finx_api_endpoint: string
```

### SDK Installation

The SDK can be installed via pip for versions >= 2.0.0
#### Python
```shell script
pip3 install fiteanalytics==2.0.0
```
#### Node.js
```
npm package coming soon - for the time being, please clone the client file.
```
### Quickstart

Here is some sample code to get you started.

#### Python
```python
import json
from fiteanalytics.finx.client import FinXClient

# Initialize synchronous HTTP client 
# 1. Credentials fetched from environment variables
finx = FinXClient()

# 2. Credentials passed directly (and carefully!)
finx = FinXClient(finx_api_key=my_api_key, finx_api_endpoint=my_api_endpoint)

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

# Batch get security reference data
print('\n*********** Batch Get Security Reference Data ***********')
batch_reference_data = finx.batch_coverage_check(
    [
        {'security_id': 'USQ98418AH10'},
        {'security_id': '3133XXP50'}
    ],
    block=True
)
print(json.dumps(batch_reference_data, indent=4))

```
#### Node.js
```javascript
import FinXClient from "fiteanalytics/finx/client";

// Initialize async HTTP client 
// 1. Credentials fetched environment variables
let finx = FinXClient();

// 2. Credentials passed directly (and carefully!)
finx = FinXClient({finx_api_key: my_api_key, finx_api_endpoint: my_api_endpoint})

let result;

async function run() {
    // Get API methods
    console.log('\n*********** API Methods ***********');
    result = await finx.get_api_methods({
        callback: async(result, kwargs={}) => console.log('API METHODS:', result)
    });
    console.log(result);

    let security_id = 'USQ98418AH10';
    let as_of_date = '2020-09-14';

    // Get security reference data
    console.log('\n*********** Security Reference Data ***********');
    result = await finx.get_security_reference_data(
        security_id,
        {
            as_of_date: as_of_date,
            callback: async(result, kwargs={}) => console.log('SECURITY REFERENCE:', result)
        }
    );
    console.log(result);
    
    // Get security analytics
    console.log('\n*********** Security Analytics ***********');
    result = await finx.get_security_analytics(
        security_id,
        {
            as_of_date: as_of_date,
            price: 100
        }
    );
    console.log(result);

    // Get security cash flows
    console.log('\n*********** Security Cash Flows ***********');
    result = await finx.get_security_cash_flows(
        security_id,
        {
            as_of_date: as_of_date,
            price: 100
        }
    );
    console.log(result);

    // Clear cache
    finx.clear_cache();

    // Batch get security reference data
    console.log('\n*********** Batch Get Security Reference Data ***********');
    result = await finx.batch(
        finx.get_security_reference_data,
        {
            'USQ98418AH10': {as_of_date: '2020-09-14'},
            '3133XXP50': {as_of_date: '2020-09-14'}
        }
    );
    console.log(result);
    return 1;
}

run().then(x => console.log(x));
```
## Python SDK
### Client Types
The Python SDK offers three different clients for using the FinX API. Each of these clients employs a highly performant 
Least-Recently-Used (LRU) cache under the hood. You can specify the maximum cache size using the ```max_cache_size``` 
keyword argument in the constructor - the default is ```100```.

When invoking a function, the client will construct a cache key from the name of the function being called and the 
parameters passed. The client then uses this key to check if a response has already been recorded in the cache, 
and returns the response if so. Otherwise, it dispatches the request to the FinX API and records the response in the 
cache once it is received. The cache may be cleared using 
```python
finx.clear_cache()
```
The cache is especially important for the WebSocket client, since responses are received and parsed asynchronously 
using callback functions. The cache serves as a store for retrieving the values for your requests.

#### Synchronous HTTP Client
Each function makes blocking synchronous requests. 
##### Initialization
```python
finx = FinXClient()
# or 
finx = FinXClient('sync')
```

#### Asynchronous HTTP Client
Each function makes asynchronous requests. Capable of dispatching multiple requests concurrently using asyncio.
##### Initialization
```python
finx = FinXClient('async')
``` 
All functions are asynchronous and must therefore be awaited.

#### WebSocket Client
Runs a WebSocket connection in a separate thread and uses the connection to send requests and receive responses.
Capable of dispatching multiple requests concurrently.
##### Initialization
```python
finx = FinXClient('socket')
```
By their nature, WebSockets are asynchronous. Function calls using this client will not return 
the API response unless the request has been cached. If the request has not been cached, the function will return the 
cache key that will be used to store the response in the cache when it is received.

For all of the WebSocket client's methods, the ```callback``` keyword argument may be used to define a function to be 
executed on the response when it is received, regardless of whether or not it was found in the cache. The function 
should take the response object as a parameter and optional keyword arguments specified in the original function call. 
**The callback will not block the main thread**. Here is an example of its usage:
```python
def my_callback(response, **kwargs):
    print(f'\nCallback got the response: {response}\n')
    print(f'Keyword arguments: {kwargs}')


finx = FinXClient('socket')
finx.get_api_methods(callback=my_callback, my_callback_kwarg='foo')
```
If you prefer not to use the callback functionality or would like to wait for the response before proceeding in your 
program, you can use the ```block=True``` keyword. This will block the main thread until the result arrives.
```python
response = finx.get_api_methods(block=True)
``` 
You can even combine the ```block``` and ```callback``` functionality. The combination will block the main thread until 
the result is received, execute the callback on the result, and return the result.
```python
response = finx.get_api_methods(block=True, callback=my_callback)
```
#### List API Functions

```
Inputs: 
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

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

#### Coverage Check
```
Inputs: 
:param security_id: string - ID of security of interest
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

Output: A object indicating if the security is covered
```
##### Example
```python
coverage = finx.coverage_check('USQ98418AH10')
print(json.dumps(coverage, indent=4))                      
```
###### Output
```json5
{
    "security_id": "USQ98418AH10",
    "is_covered": true
}

```

#### Get Security Reference Data
```
Inputs:
:param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD. Default None, optional
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

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
:keyword as_of_date: string as YYYY-MM-DD. Default None, optional
:keyword price: float Default None, optional
:keyword volatility: float. Default None, optional
:keyword yield_shift: int. Default None, optional
:keyword shock_in_bp: int. Default None, optional
:keyword horizon_months: uint. Default None, optional
:keyword income_tax: float. Default None, optional
:keyword cap_gain_short_tax: float. Default None, optional
:keyword cap_gain_long_tax: float. Default None, optional
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

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
:keyword as_of_date: string as YYYY-MM-DD. Default None, optional
:keyword price: float. Default 100.0, optional
:keyword shock_in_bp: int. Default None, optional
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

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

### Javascript SDK

The Javascript SDK is similarly implemented as a wrapper class with member functions for invoking the various API 
methods, however, all methods are implemented as asynchronous functions and must be invoked accordingly. Key word arguments 
for the constructor and all functions must be specified using a key-value object since key words are not natively 
supported by javascript.

Ensure you have installed the packages listed in package.json:
```shell script
cd ~/sdk/node
npm install
```

#### Get API Methods

```
Inputs:
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

Output: An object mapping each available API method to their respective required and optional parameters
```

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

```
Inputs
:param security_id: (string)
:param as_of_date: (string as YYYY-MM-DD) optional
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

Output: An object containing various descriptive fields for the specified security
```

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

```
Inputs:
:param security_id: (string)
:keyword as_of_date: (string as YYYY-MM-DD) optional
:keyword price: (float) optional
:keyword volatility: (float) optional
:keyword yield_shift: (int basis points) optional
:keyword shock_in_bp: (int basis points) optional
:keyword horizon_months: (uint) optional
:keyword income_tax: (float) optional
:keyword cap_gain_short_tax: (float) optional
:keyword cap_gain_long_tax: (float) optional
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

Output: An object containing various fixed income risk analytics measures for the specified security and parameters

```

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

```
Inputs:
:param security_id: (string)
:keyword as_of_date: (string as YYYY-MM-DD) optional
:keyword price: (float) optional
:keyword shock_in_bp: (int) optional
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

Output: An object containing a vector time series of cash flow dates and corresponding amounts
```

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

```
Inputs:
:param function: (function) Client member function to invoke for each security
:param security_args: (dict) Object mapping security_id (string) to an object of key word arguments 
:keyword callback: callable - websocket client only. Default None, optional
:keyword block: bool - websocket client only: block main thread until result arrives and return the value. Default False, optional

Output: A list of corresponding results for each security ID specified
```

##### Example
```javascript
reference_data = finx.batch(
    finx.get_security_reference_data, 
    {
        'USQ98418AH10': {as_of_date: '2020-09-14'}, 
        '3133XXP50': {as_of_date: '2020-09-14'}   
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
