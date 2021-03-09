#! Python
"""
finx.py
"""
import yaml
import asyncio
import aiohttp
import requests
from os import getenv
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor


class SyncFinX:

    def __init__(self, **kwargs):
        """
        Client constructor accepts 2 distinct methods for passing credentials named FINX_API_KEY and FINX_API_ENDPOINT

        :keyword yaml_path: path to YAML file
        :keyword env_path: path to .env file

        If yaml_path not passed, loads env_path (if passed) then checks environment variables
        """
        yaml_path = kwargs.get('yaml_path')
        if yaml_path is not None:
            config = yaml.safe_load(open(yaml_path))
            self.__api_key = config.get('FINX_API_KEY')
            self.__api_url = config.get('FINX_API_ENDPOINT')
        else:
            env_path = kwargs.get('env_path')
            if env_path is not None:
                try:
                    load_dotenv(env_path)
                except Exception as e:
                    print(f'Could not load .env file at {env_path}: {e}')
            self.__api_key = getenv('FINX_API_KEY')
            self.__api_url = getenv('FINX_API_ENDPOINT')
        if self.__api_key is None:
            raise Exception('API key not found')
        if self.__api_url is None:
            self.__api_url = 'https://sandbox.finx.io/api/'
        self.__session = requests.session()

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    def __dispatch(self, request_body):
        return self.__session.post(self.__api_url, data=request_body).json()

    def get_api_methods(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'list_api_functions'
        })

    def get_security_reference_data(self, security_id, as_of_date=None, **kwargs):
        """
        Security reference function

        :param security_id: string
        :param as_of_date: string as YYYY-MM-DD (optional)
        """
        return self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'security_reference',
            'security_id': security_id,
            'as_of_date': as_of_date
        })

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
            **{arg: value for arg, value in kwargs.items() if value is not None}
        })

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
            'security_id': security_id,
            **{arg: value for arg, value in kwargs.items() if value is not None}
        })

    def batch(self, function, security_ids, **kwargs):
        assert type(security_ids) is list and len(security_ids) < 100
        executor = ThreadPoolExecutor()
        tasks = [executor.submit(function, **{'security_id': security_id, **kwargs})
                 for security_id in security_ids[:100]]
        return [task.result() for task in tasks]


class AsyncFinx(SyncFinX):

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

    async def __dispatch(self, request_body):
        if self.__session is None:
            self.__session = aiohttp.ClientSession()
        async with self.__session.post(self.__api_url, data=request_body) as response:
            return await response.json()

    async def get_api_methods(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return await self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'list_api_functions'
        })

    async def get_security_reference_data(self, security_id, as_of_date=None, **kwargs):
        """
        Security reference function

        :param security_id: string
        :param as_of_date: string as YYYY-MM-DD (optional)
        """
        return await self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'security_reference',
            'security_id': security_id,
            'as_of_date': as_of_date
        })

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
            **{arg: value for arg, value in kwargs.items() if value is not None}
        })

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
            **{arg: value for arg, value in kwargs.items() if value is not None}
        })

    async def batch(self, function, security_ids, **kwargs):
        """
        Invoke function for batch of securities
        :param function: Client member function
        :param security_ids: List of security IDs (max 100)
        :param kwargs: Relevant key words for function
        :return:
        """
        assert type(security_ids) is list
        try:
            asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        tasks = [function(security_id=security_id, **kwargs) for security_id in security_ids[:100]]
        return await asyncio.gather(*tasks)


def FinX(**kwargs):
    """
    Unified interface to spawn FinX client. Use keyword asyncio=True to specify the async client
    :keyword asyncio: bool (default False)
    """
    return AsyncFinx(**kwargs) if kwargs.get('asyncio') not in [None, False] else SyncFinX(**kwargs)
