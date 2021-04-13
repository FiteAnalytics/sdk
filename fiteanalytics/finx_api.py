#! Python
"""
finx_api.py
"""
import os
import json
import asyncio
from gc import collect
import _thread as thread
from requests import session
from aiohttp import ClientSession
from urllib.parse import urlparse
from websocket import WebSocketApp
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

DEFAULT_API_URL = 'https://sandbox.finx.io/api/'


class LRUCache(OrderedDict):
    """
    Least Recently Used (LRU) cache
    """
    def __init__(self, maxsize=128, *args, **kwds):
        self.maxsize = maxsize
        super().__init__(*args, **kwds)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


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
            raise Exception('API key not found - please include the keyword argument finx_api_key or set the '
                            'environment variable FINX_API_KEY')
        if self.__api_url is None:
            self.__api_url = DEFAULT_API_URL
        self.session = session()
        self.max_cache_size = kwargs.get('max_cache_size')
        if self.max_cache_size is None:
            self.max_cache_size = 100
        self.cache = LRUCache(self.max_cache_size)

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    @staticmethod
    def __get_cache_key(params):
        return '_'.join([f'{key}:{params[key]}' for key in sorted(params.keys()) if key != 'finx_api_key'])

    def clear_cache(self):
        self.cache.clear()
        collect()
        return None

    def __dispatch(self, request_body, **kwargs):
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        cache_key = self.__get_cache_key(request_body)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            return cached_response
        data = self.session.post(self.__api_url, data=request_body).json()
        error = data.get('error')
        if error is not None:
            print(f'API returned error: {error}')
            return data
        self.cache[cache_key] = data
        return data

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
            'use_kalotay_analytics': False
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
        """
        Invoke function for batch of securities
        :param function: Client member function to invoke for each security
        :param security_args: Dict mapping dict mapping security_id (string) to a dict of key word arguments
        """
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
        self.session = None

    async def __dispatch(self, request_body, **kwargs):
        if self.session is None:
            self.session = ClientSession()
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        cache_key = self.__get_cache_key(request_body)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            return cached_response
        async with self.session.post(self.__api_url, data=request_body) as response:
            data = await response.json()
            error = data.get('error')
            if error is not None:
                print(f'API returned error: {error}')
                return response
            self.cache[cache_key] = data
            return data

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
            'use_kalotay_analytics': False
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


class __FinXSocket(WebSocketApp):

    def __init__(self, **kwargs):
        """
        Client constructor supports multiple methods for passing credentials

        :keyword finx_api_key: string (handle with care)
        :keyword finx_api_endpoint: string
        :keyword env_path: string

        If yaml_path not passed, loads env_path (if passed) then checks environment variables
        """
        self.__api_key = kwargs.get('finx_api_key')
        self.__api_url = kwargs.get('finx_api_endpoint')
        if self.__api_key is None:
            self.__api_key = os.environ.get('FINX_API_KEY')
            self.__api_url = os.environ.get('FINX_API_ENDPOINT')
        if self.__api_key is None:
            raise Exception('API key not found - please include the keyword argument finx_api_key or set the '
                            'environment variable FINX_API_KEY')
        if self.__api_url is None:
            self.__api_url = DEFAULT_API_URL
        self.max_cache_size = kwargs.get('max_cache_size')
        if self.max_cache_size is None:
            self.max_cache_size = 100
        self.cache = LRUCache(self.max_cache_size)
        self.executor = ThreadPoolExecutor()

        def on_open(socket):
            try:
                params = {'finx_api_key': socket.get_api_key()}
                print(f'Sending {params}...')
                socket.send(json.dumps({'finx_api_key': socket.get_api_key()}))
            except Exception as _e:
                print(f'Socket on_open error: {_e}')
            return None

        def on_message(socket, message):
            try:
                message = json.loads(message)
                print(message)
                if message.get('is_authenticated'):
                    print(f'Successfully authenticated')
                    return None
                error = message.get('error')
                if error is not None:
                    print(f'API returned error: {error}')
                    return None
                self.cache[self.__get_cache_key(message['input_params'])] = message['data']
            except Exception as _e:
                print(f'Socket on_message error: {_e}')
            return None

        def on_close(socket):
            print('Socket closed')

        endpoint = urlparse(self.__api_url).netloc + '/ws/api/'
        try:
            url = f'ws://{endpoint}'
            print(f'Connecting to {url}')
            super().__init__(url=url, on_open=on_open, on_message=on_message, on_close=on_close)
        except Exception as e:
            print(f'Could not connect to WSS endpoint: {e}; trying WS...')
            url = f'wss://{endpoint}'
            print(f'Connecting to {url}')
            super().__init__(url=url, on_open=on_open, on_message=on_message, on_close=on_close)
        thread.start_new_thread(self.run_forever, (), {'ping_interval': 60})

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    @staticmethod
    def __get_cache_key(params):
        return '_'.join([f'{key}:{params[key]}' for key in sorted(params.keys())])

    def clear_cache(self):
        self.cache.clear()
        collect()
        return None

    def await_result(self, cache_key, callback, **kwargs):
        result = None
        while result is None:
            result = self.cache.get(cache_key)
        callback(result, **kwargs)

    def __dispatch(self, payload, **kwargs):
        callback = kwargs.pop('callback', None)
        if any(kwargs):
            payload.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        cache_key = self.__get_cache_key(payload)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            if callable(callback):
                callback(cached_response, **kwargs)
            return cached_response
        self.send(json.dumps(payload))
        if callable(callback):
            self.executor.submit(self.await_result, cache_key, callback, **kwargs)
        return cache_key

    def get_api_methods(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return self.__dispatch({'api_method': 'list_api_functions'}, **kwargs)

    def get_security_reference_data(self, security_id, as_of_date=None, **kwargs):
        """
        Security reference function

        :param security_id: string
        :param as_of_date: string as YYYY-MM-DD (optional)
        """
        payload = {
            'api_method': 'security_reference',
            'security_id': security_id,
        }
        if as_of_date is not None:
            payload['as_of_date'] = as_of_date
        return self.__dispatch(payload, **kwargs)

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
            'api_method': 'security_analytics',
            'security_id': security_id,
            'use_kalotay_analytics': False
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
            'api_method': 'security_cash_flows',
            'security_id': security_id
        }, **kwargs)

    def batch(self, function, security_args):
        """
        Invoke function for batch of securities
        :param function: Client member function to invoke for each security
        :param security_args: Dict mapping dict mapping security_id (string) to a dict of key word arguments
        """
        assert function != self.get_api_methods and type(security_args) is dict and len(security_args) < 100
        return [function(security_id, **kwargs) for security_id, kwargs in security_args.items()]


def FinX(**kwargs):
    """
    Unified interface to spawn FinX client. Use keyword "kind" to specify the type of client
    :keyword kind: (string) - 'socket' for websocket client, 'async' for async client, default sync client
    """
    kind = kwargs.pop('kind', None)
    if kind == 'socket':
        return __FinXSocket(**kwargs)
    if kind == 'async':
        return __AsyncFinx(**kwargs)
    return __SyncFinX(**kwargs)
