#! Python
"""
finx_api.py
"""
import os
import yaml
import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor

DEFAULT_API_URL = 'https://sandbox.finx.io/api/'


class __SyncFinX:

    def __init__(self, **kwargs):
        """
        Client constructor supports multiple methods for passing credentials

        :keyword finx_api_key: string (handle with care)
        :keyword finx_api_endpoint: string
        :keyword yaml_path: string
        :keyword env_path: string

        If yaml_path not passed, loads env_path (if passed) then checks environment variables
        """
        self.__api_key = kwargs.get('finx_api_key')
        self.__api_url = kwargs.get('finx_api_endpoint')
        if self.__api_key is None:
            self.__api_key = os.environ.get('FINX_API_KEY')
            self.__api_url = os.environ.get('FINX_API_ENDPOINT')
        if self.__api_key is None:
            raise Exception('API key not found - please include as a kwarg "finx_api_key" OR set the environment variable: FINX_API_KEY')
        if self.__api_url is None:
            self.__api_url = DEFAULT_API_URL
        self.__session = requests.session()

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    def __dispatch(self, request_body, **kwargs):
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        return self.__session.post(self.__api_url, data=request_body).json()

    def get_api_methods(self):
        """
        List API methods with parameter specifications
        """
        return self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'list_api_functions'
        })

    def get_security_reference_data(self, security_id, as_of_date=None):
        """
        Security reference function

        :param security_id: string
        :param as_of_date: string as YYYY-MM-DD (optional)
        """
        request_body = {
            'finx_api_key': self.__api_key,
            'api_method': 'security_reference',
            'security_id': security_id,
        }
        if as_of_date is not None:
            request_body['as_of_date'] = as_of_date
        return self.__dispatch(request_body)

    def get_security_analytics(self, security_id, **kwargs):
        """
        Security analytics function

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
        """
        return self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'security_analytics',
            'security_id': security_id,
        }, **kwargs)

    def get_security_cash_flows(self, security_id, **kwargs):
        """
        Security cash flows function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD (optional)
        :keyword price: float (optional)
        :keyword shock_in_bp: int (optional)
        """
        return self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'security_cash_flows',
            'security_id': security_id
        }, **kwargs)

    def batch(self, function, security_args):
        assert function != self.get_api_methods and type(security_args) is dict and len(security_args) < 100
        executor = ThreadPoolExecutor()
        tasks = [executor.submit(function, security_id=security_id, **kwargs)
                 for security_id, kwargs in security_args.items()]
        return [task.result() for task in tasks]


class __AsyncFinx(__SyncFinX):

    def __init__(self, **kwargs):
        """
        Client constructor accepts 2 distinct methods for passing credentials named FINX_API_KEY and FINX_API_ENDPOINT

        :keyword yaml_path: path to YAML file
        :keyword env_path: path to .env file

        If yaml_path not passed, loads env_path (if passed) then checks environment variables
        """
        super().__init__(**kwargs)
        self.__api_key = self.get_api_key()
        self.__api_url = self.get_api_url()
        self.__session = None

    async def __dispatch(self, request_body, **kwargs):
        if self.__session is None:
            self.__session = aiohttp.ClientSession()
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        async with self.__session.post(self.__api_url, data=request_body) as response:
            return await response.json()

    async def get_api_methods(self):
        """
        List API methods with parameter specifications
        """
        return await self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'list_api_functions'
        })

    async def get_security_reference_data(self, security_id, as_of_date=None):
        """
        Security reference function

        :param security_id: string
        :param as_of_date: string as YYYY-MM-DD (optional)
        """
        request_body = {
            'finx_api_key': self.__api_key,
            'api_method': 'security_reference',
            'security_id': security_id,
        }
        if as_of_date is not None:
            request_body['as_of_date'] = as_of_date
        return await self.__dispatch(request_body)

    async def get_security_analytics(self, security_id, **kwargs):
        """
        Security analytics function

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
        """
        return await self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'security_analytics',
            'security_id': security_id,
        }, **kwargs)

    async def get_security_cash_flows(self, security_id, **kwargs):
        """
        Security cash flows function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD (optional)
        :keyword price: float (optional)
        :keyword shock_in_bp: int (optional)
        """
        return await self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'security_cash_flows',
            'security_id': security_id,
        }, **kwargs)

    async def batch(self, function, security_args):
        """
        Invoke function for batch of securities
        :param function: Client member function to invoke for each security
        :param security_args: Dict mapping dict mapping security_id (string) to a dict of key word arguments
        """
        assert function != self.get_api_methods and type(security_args) is dict
        try:
            asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        tasks = [function(security_id=security_id, **kwargs) for security_id, kwargs in security_args.items()]
        return await asyncio.gather(*tasks)


def FinXClient(**kwargs):
    """
    Unified interface to spawn FinX client. Use keyword asyncio=True to specify the async client
    :keyword asyncio: bool (default False)
    """
    return __AsyncFinx(**kwargs) if kwargs.get('asyncio') else __SyncFinX(**kwargs)
