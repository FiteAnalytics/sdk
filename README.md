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
# Fite Analytics Configuration
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

## Python SDK

The Python SDK is a python package that contains various functions to interact with the Fite Analtyics cloud platform.

### Installing Python SDK

### Using Python SDK

Once the configuration file is edited and saved, you may import the python library into your command line or python application. The location of the configuration 
by default is alongside the python package in the same directory, but you may change the location of the configuration file with a function in the library itself.


### fiteanalytics.py python package

The fiteanalytics.py package contains various functions for interacting with the Fite Analytics platform.

#### hello world

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

#### security reference

#### security analytics

## Javascript SDK

We expect the Javascript SDK to be available in early Q2 2021.
