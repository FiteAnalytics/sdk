# Fite Analytics Software Development Kit (SDK)

## Introduction

This document details how to use the SDK to interact with Fite Analytics' services. Please refer to this document as the definitive
source of information.

For questions or comments please contact us [via email](mailto:info@fiteanalytics.com) or on [reddit](https://www.reddit.com/r/fiteanalytics/).

## FinX API SDK
The FinX API is a RESTful API endpoint offering rich fixed income analytics calculations, including security reference data, interest rate risk metrics, and projected cash flows. The Fite Analytics SDK offers a client class implementation for a variety of programming languages to wrap access to the API methods. Unless specified otherwise, each language's client implementation consist solely of one implementation file containing all the necessary code to expose the API functions.

The FinX API requires an API key for usage. You may also be provided with a specific URL for accessing services. Please contact us [via email](mailto:info@fiteanalytics.com) to obtain your key. We require three fields to validate your credentials: `VERSION`, `FINX_API_KEY` and `FINX_API_ENDPOINT`. Note that these keys are case sensitive. The SDK facilitates two distinct methods for securely passing credentials to the API clients.

The first method is via a YAML configuration file containing your credentials. You may give the path to this file when initializing the client:
### YAML configuration syntax
```
VERSION: 1
FINX_API_KEY: my_finx_key
FINX_API_ENDPOINT: https://api.finx.io
```
The second method looks for the required credentials in environment variables. If a .env file is specified in the client initialization, the .env file will be loaded before checking the variables.
### .env file syntax
```
VERSION=1
FINX_API_KEY=my_finx_key
FINX_API_ENDPOINT=https://api.finx.io
```

### SDK Installation

For the immediate future, please clone this repository into your project to begin using the SDK.
```
git clone https://github.com/FiteAnalytics/sdk
```

### Python SDK

The Python SDK is implemented as a wrapper class with member functions for invoking the various API methods.

#### Initialization

##### Inputs

1. YAML configuration file formatted as described above (optional)
2. .env file formatted as described above (optional)

##### Output

Returns a class object with member functions for invoking the various API methods

##### Example
```
>>> from finx_api.finx import FinX

# YAML configuration file
>>> finx = FinX(yaml_path='path/to/file.yml')

# .env file
>>> finx = FinX(env_path='path/to/.env')

# No file (will check environment variables)
>>> finx = FinX()
```

#### Get API Methods

##### Inputs

None

##### Output

A object mapping each available API method to their respective required and optional parameters

##### Example
```
>>> finx.get_api_methods()
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
```
>>> finx.get_security_reference_data('USQ98418AH10', '2020-09-14')
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
:param security_id: string (required)
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
```
>>> finx.get_security_analytics(security_id='USQ98418AH10', as_of_date='2020-09-14', price=100)
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
```
>>> finx.get_security_cash_flows(security_id='USQ98418AH10', as_of_date='2020-09-14', price=100)
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

### Javascript SDK

The Javascript SDK is similarly implemented as a wrapper class with member functions for invoking the various API 
methods, however, all methods are implemented as asynchronous functions and must used accordingly. Key word arguments 
must be specified within a single map object argument for the security analytics and security cash flows functions since
key words are not natively supported by javascript.

#### Initialization

##### Inputs

1. YAML configuration file formatted as described above (optional)
2. .env file formatted as described above (optional)

##### Output

Returns a class object with member functions for invoking the various API methods

##### Example
```
import FinX from "../finx_api/finx.js";

// YAML configuration
let finx = FinX('finx_api/finx_config.yml');

// .env file
finx = FinX(null, env_path='path/to/.env');

// No file (will check environment variables);
finx = FinX()
```

#### Get API Methods

##### Inputs

None

##### Output

A object mapping each available API method to their respective required and optional parameters

##### Example
```
finx.get_api_methods().then(data => console.log(data));
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
```
finx.get_security_reference_data('USQ98418AH10', '2020-09-14').then(data => console.log(data));
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
:param security_id: string (required)
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
```
finx.get_security_analytics('USQ98418AH10', {as_of_date: '2020-09-14', price: 100}).then(data => console.log(data));
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
```
finx.get_security_cash_flows('USQ98418AH10', {as_of_date: '2020-09-14', price: 100}).then(data => console.log(data));
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
