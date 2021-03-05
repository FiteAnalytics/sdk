# Fite Analytics Software Development Kit (SDK)

## Introduction

This document details how to use the SDK to interact with Fite Analytics' services. Please refer to this document as the definitive
source of information.

For questions or comments please contact us [via email](mailto:info@fiteanalytics.com) or on [reddit](https://www.reddit.com/r/fiteanalytics/).

## Python SDK

The Python SDK is a python package that contains various functions to interact with the Fite Analtyics cloud platform.

### Installing Python SDK

### Using Python SDK

The python SDK package contains 2 files: a python library (fiteanalytics.py) and a configuration file (fiteanalytics.yml). You must populate the 
fiteanalytics.config configuration file with your particular information.

Once the configuration file is edited and saved, you may import the python library into your command line or python application. The location of the configuration 
by default is alongside the python package in the same directory, but you may change the location of the configuration file with a function in the library itself.

### fiteanalytics.cfg configuration file

The configuration file is YAML and controls the variables used by the python library.

#### configuration file syntax

##### fiteanalytics.yml
```
# Fite Analytics Configuration
- version: 1
- finx_api_key: my_finx_key
- finx_api_endpoint: https://api.finx.io
```

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
