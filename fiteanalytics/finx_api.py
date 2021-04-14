#! Python
"""
finx_api.py
"""
import os
import time
import json
import asyncio
from lru import LRU
from gc import collect
import _thread as thread
from requests import session
from aiohttp import ClientSession
from urllib.parse import urlparse
from websocket import WebSocketApp
from concurrent.futures import ThreadPoolExecutor

DEFAULT_API_URL = 'https://sandbox.finx.io/api/'


def _get_cache_key(params):
    return ','.join([f'{key}:{params[key]}' for key in sorted(params.keys())])


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
        self.cache = LRU(self.max_cache_size)

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

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
        cache_key = _get_cache_key(request_body)
        cached_response = self.cache.get(cache_key, None)
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

    def get_api_methods(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'list_api_functions'
        })

    def get_security_reference_data(self, security_id, **kwargs):
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
        as_of_date = kwargs.get('as_of_date')
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
        cache_key = _get_cache_key(request_body)
        cached_response = self.cache.get(cache_key, None)
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

    async def get_api_methods(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return await self.__dispatch({
            'finx_api_key': self.__api_key,
            'api_method': 'list_api_functions'
        })

    async def get_security_reference_data(self, security_id, **kwargs):
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
        as_of_date = kwargs.get('as_of_date')
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
        self.cache = LRU(self.max_cache_size)
        self.executor = ThreadPoolExecutor()
        self.is_authenticated = False

        def on_open(socket):
            try:
                print(f'Socket connected. Authenticating...')
                socket.send(json.dumps({'finx_api_key': socket.get_api_key()}))
            except Exception as _e:
                print(f'Socket on_open error: {_e}')
            return None

        def on_message(socket, message):
            try:
                message = json.loads(message)
                # print(message)
                if message.get('is_authenticated'):
                    print('Successfully authenticated')
                    self.is_authenticated = True
                    return None
                error = message.get('error')
                if error is not None:
                    print(f'API returned error: {error}')
                    return None
                self.cache[message['cache_key']] = message['data']
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
        # self.executor.submit(self.run_forever, ping_interval=60)
        thread.start_new_thread(self.run_forever, (), {'ping_interval': 60})

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    def clear_cache(self):
        self.cache.clear()
        collect()
        return None

    def await_result(self, cache_key, callback, **kwargs):
        result = None
        while result is None:
            result = self.cache.get(cache_key, None)
        callback(result, **kwargs)

    def __dispatch(self, payload, **kwargs):
        if not self.is_authenticated:
            i = 5000
            while not self.is_authenticated and i >= 1:
                time.sleep(.001)
                i -= 1
            if not self.is_authenticated:
                raise Exception('Client not authenticated')
        callback = kwargs.pop('callback', None)
        if any(kwargs):
            payload.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        cache_key = _get_cache_key(payload)
        cached_response = self.cache.get(cache_key, None)
        if cached_response is not None:
            print('Found in cache')
            if callable(callback):
                callback(cached_response, **kwargs)
            return cached_response
        payload['cache_key'] = cache_key
        self.send(json.dumps(payload))
        if callable(callback):
            self.executor.submit(self.await_result, cache_key, callback, **kwargs)
        return cache_key

    def get_api_methods(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return self.__dispatch({'api_method': 'list_api_functions'}, **kwargs)

    def get_security_reference_data(self, security_id, **kwargs):
        """
        Security reference function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD (optional)
        """
        payload = {
            'api_method': 'security_reference',
            'security_id': security_id,
        }
        as_of_date = kwargs.get('as_of_date')
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


def FinX(kind='sync', **kwargs):
    """
    Unified interface to spawn FinX client. Use keyword "kind" to specify the type of client
    :keyword kind: (string) - 'socket' for websocket client, 'async' for async client, default sync client
    """
    if kind == 'socket':
        return __FinXSocket(**kwargs)
    if kind == 'async':
        return __AsyncFinx(**kwargs)
    return __SyncFinX(**kwargs)


"""
from timeit import timeit

def sync_client_test():
    from finx_api import FinX
    finx = FinX('sync')
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    finx.get_api_methods()
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    finx.get_security_analytics('9127962F5', as_of_date='2021-03-24')
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24')
    finx.clear_cache()
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    finx.batch(
        finx.get_security_analytics, 
        {
            '9127962F5': {'as_of_date': '2021-03-24', 'foo': 'bar'},
            'USQ98418AH10': {'as_of_date': '2020-09-14'},
            '912796B24': {'as_of_date': '2021-04-01'},
            '912796F61': {'as_of_date': '2021-04-01'}
        }
    )
    finx.session.close()
"""
"""
timeit(lambda: sync_client_test(), number=1)
"""
"""
from asgiref.sync import AsyncToSync

@AsyncToSync
async def async_client_test():
    from finx_api import FinX
    finx = FinX('async')
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    await finx.get_api_methods(
        callback=lambda x, **kwargs: print(f'\n====> GOT API METHODS: {x}\n'))
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    await finx.get_security_analytics(
        '9127962F5', 
        as_of_date='2021-03-24', 
        callback=lambda x, **kwargs: print(f'\n====> GOT SECURITY ANALYTICS: {x}\n'))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    await finx.get_security_cash_flows(
        '9127962F5', 
        as_of_date='2021-03-24', 
        callback=lambda x, **kwargs: print(f'\n====> GOT SECURITY CASH FLOWS: {x}\n'))
    finx.clear_cache()
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    await finx.batch(
        finx.get_security_analytics, 
        {
            '9127962F5': {'as_of_date': '2021-03-24', 'foo': 'bar'},
            'USQ98418AH10': {'as_of_date': '2020-09-14'},
            '912796B24': {'as_of_date': '2021-04-01'},
            '912796F61': {'as_of_date': '2021-04-01'}
        }
    )
    await finx.session.close()
"""
"""
timeit(lambda: async_client_test(), number=1)
"""
"""
from timeit import timeit
import time

def socket_client_test():
    from finx_api import FinX
    finx = FinX('socket')
    keys = []
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    keys.append(finx.get_api_methods())
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    keys.append(finx.get_security_analytics('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    keys.append(finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    keys += finx.batch(
        finx.get_security_analytics, 
        {
            '9127962F5': {'as_of_date': '2021-03-24', 'foo': 'bar'},
            'USQ98418AH10': {'as_of_date': '2020-09-14'},
            '912796B24': {'as_of_date': '2021-04-01'},
            '912796F61': {'as_of_date': '2021-04-01'}
        }
    )
    i = 15000
    results = {key: finx.cache.get(key) for key in keys}
    remaining_tasks = {key: value for key, value in results.items() if value is None}
    while any(remaining_tasks) and i >= 1:
        time.sleep(0.001)
        i -=1
        results = {key: finx.cache.get(key) for key in remaining_tasks}
        remaining_tasks = {key: value for key, value in results.items() if value is None}
    if any(remaining_tasks):
        print(f'Didn\'t get results in time for {len(remaining_tasks.keys())} out of {len(keys)} tasks')
"""
"""
timeit(lambda: socket_client_test(), number=1)
"""