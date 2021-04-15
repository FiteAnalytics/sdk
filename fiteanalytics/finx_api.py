#! Python
"""
finx_api.py
"""
import os
import time
import json
import asyncio
import traceback
from lru import LRU
from gc import collect
from requests import session
from threading import Thread
from aiohttp import ClientSession
from urllib.parse import urlparse
from websocket import WebSocketApp
from concurrent.futures import ThreadPoolExecutor

DEFAULT_API_URL = 'https://sandbox.finx.io/api/'


def _get_cache_key(params):
    return ','.join([f'{key}:{params[key]}' for key in sorted(params.keys())])


class _FinX:

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint, or FINX_API_KEY and FINX_API_ENDPOINT
        environment variables
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
        self._session = session() if kwargs.get('session') else None
        self._executor = ThreadPoolExecutor() if kwargs.get('no_executor') else None

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    def clear_cache(self):
        self.cache.clear()
        collect()
        return None

    def _dispatch(self, request_body, **kwargs):
        assert self._session is not None
        request_body['finx_api_key'] = self.__api_key
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        cache_key = _get_cache_key(request_body)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            return cached_response
        data = self._session.post(self.__api_url, data=request_body).json()
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
        return self._dispatch({'api_method': 'list_api_functions'}, **kwargs)

    def get_security_reference_data(self, security_id, **kwargs):
        """
        Security reference function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD (optional)
        """
        request_body = {
            'api_method': 'security_reference',
            'security_id': security_id,
        }
        as_of_date = kwargs.get('as_of_date')
        if as_of_date is not None:
            request_body['as_of_date'] = as_of_date
        return self._dispatch(request_body, **kwargs)

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
        return self._dispatch({
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
        return self._dispatch({
            'api_method': 'security_cash_flows',
            'security_id': security_id
        }, **kwargs)

    def batch(self, function, security_args):
        """
        Invoke function for batch of securities
        :param function: Client member function to invoke for each security
        :param security_args: Dict mapping dict mapping security_id (string) to a dict of key word arguments
        """
        assert self._executor is not None \
            and function != self.get_api_methods \
            and type(security_args) is dict \
            and len(security_args) < 100
        tasks = [self._executor.submit(function, security_id=security_id, **kwargs)
                 for security_id, kwargs in security_args.items()]
        return [task.result() for task in tasks]


class _AsyncFinx(_FinX):

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint, or FINX_API_KEY and FINX_API_ENDPOINT
        environment variables
        """
        super().__init__(**kwargs, session=False, executor=False)
        self.__api_key = self.get_api_key()
        self.__api_url = self.get_api_url()
        self._session = None

    async def _dispatch(self, request_body, **kwargs):
        request_body['finx_api_key'] = self.__api_key
        if self._session is None:
            self._session = ClientSession()
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        cache_key = _get_cache_key(request_body)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            return cached_response
        async with self._session.post(self.__api_url, data=request_body) as response:
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
        return await self._dispatch({'api_method': 'list_api_functions'})

    async def get_security_reference_data(self, security_id, **kwargs):
        """
        Security reference function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD (optional)
        """
        request_body = {
            'api_method': 'security_reference',
            'security_id': security_id,
        }
        as_of_date = kwargs.get('as_of_date')
        if as_of_date is not None:
            request_body['as_of_date'] = as_of_date
        return await self._dispatch(request_body)

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
        return await self._dispatch({
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
        return await self._dispatch({
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


class _FinXSocket(_FinX):

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint, or FINX_API_KEY and FINX_API_ENDPOINT
        environment variables
        """
        super().__init__(**kwargs, session=False)
        self.__api_key = super().get_api_key()
        self.__api_url = super().get_api_url()
        self.is_authenticated = False

        def on_open(socket):
            try:
                print(f'Socket connected. Authenticating...')
                self.__socket.send(json.dumps({'finx_api_key': self.__api_key}))
            except Exception as e:
                print(f'Socket on_open error: {e}')
            return None

        def on_message(socket, message):
            try:
                message = json.loads(message)
                if message.get('is_authenticated'):
                    print('Successfully authenticated')
                    self.is_authenticated = True
                    return None
                error = message.get('error')
                if error is not None:
                    print(f'API returned error: {error}')
                self.cache[message['cache_key']] = message['data'] if 'data' in message else message['error']
            except Exception as e:
                print(f'Socket on_message error: {e}')
            return None

        on_close = lambda socket: print('Socket closed')
        endpoint = urlparse(self.__api_url).netloc + '/ws/api/'
        protocol = 'wss' if kwargs.get('ssl') else 'ws'
        url = f'{protocol}://{endpoint}'
        try:
            print(f'Connecting to {url}')
            self.__socket = WebSocketApp(url, on_open=on_open, on_message=on_message, on_close=on_close)
        except Exception as e:
            raise Exception(f'Failed to connect: {e}')
        thread = Thread(target=self.__socket.run_forever, kwargs={'ping_interval': 60}, daemon=True)
        thread.start()

    def _await_result(self, cache_key, callback, **kwargs):
        try:
            result = None
            while result is None:
                result = self.cache.get(cache_key)
            callback(result, **kwargs)
        except:
            print(traceback.format_exc())

    def _dispatch(self, payload, **kwargs):
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
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            if callable(callback):
                callback(cached_response, **kwargs)
            return cached_response
        payload['cache_key'] = cache_key
        self.__socket.send(json.dumps(payload))
        if callable(callback):
            self._executor.submit(self._await_result, cache_key, callback, **kwargs)
        return cache_key

    def batch(self, function, security_args, **kwargs):
        """
        Invoke function for batch of securities
        :param function: Client member function to invoke for each security
        :param security_args: Dict mapping dict mapping security_id (string) to a dict of key word arguments
        :keyword callback: function to invoke on each corresponding result when received
        """
        assert function != self.get_api_methods and type(security_args) is dict and len(security_args) < 100
        return [function(security_id, **_security_args, **kwargs)
                for security_id, _security_args in security_args.items()]


def FinX(**kwargs):
    """
    Unified interface to spawn FinX client. Use keyword "kind" to specify the type of client
    :keyword kind: (string) - 'socket' for websocket client, 'async' for async client, default sync client
    """
    kind = kwargs.pop('kind', 'sync')
    if kind == 'socket':
        return _FinXSocket(**kwargs)
    if kind == 'async':
        return _AsyncFinx(**kwargs)
    return _FinX(**kwargs)


"""
import time
import asyncio
from timeit import timeit
from finx_api import FinX
from asgiref.sync import AsyncToSync

def sync_client_test():
    finx = FinX()
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
    finx._session.close()
    

@AsyncToSync
async def async_client_test():
    finx = FinX(kind='async')
    tasks = []
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    tasks.append(finx.get_api_methods(
        callback=lambda x, **kwargs: print(f'\n====> GOT API METHODS: {x}\n')))
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    tasks.append(finx.get_security_analytics(
        '9127962F5', 
        as_of_date='2021-03-24', 
        callback=lambda x, **kwargs: print(f'\n====> GOT SECURITY ANALYTICS: {x}\n')))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    tasks.append(finx.get_security_cash_flows(
        '9127962F5', 
        as_of_date='2021-03-24', 
        callback=lambda x, **kwargs: print(f'\n====> GOT SECURITY CASH FLOWS: {x}\n')))
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    tasks.append(finx.batch(
        finx.get_security_analytics, 
        {
            '9127962F5': {'as_of_date': '2021-03-24', 'foo': 'bar'},
            'USQ98418AH10': {'as_of_date': '2020-09-14'},
            '912796B24': {'as_of_date': '2021-04-01'},
            '912796F61': {'as_of_date': '2021-04-01'}
        }
    ))
    await asyncio.gather(*tasks)
    await finx._session.close()
    
    
def socket_client_test():
    finx = FinX(kind='socket')
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
    remaining_tasks = {key: finx.cache.get(key) for key in keys}
    keys = []
    for key, value in remaining_tasks.items():
        if value is not None:
            print(f'Got {key}')
        else:
            keys.append(key)
    while any(remaining_tasks) and i >= 1:
        time.sleep(0.001)
        i -=1
        remaining_tasks = {key: finx.cache.get(key) for key in keys}
        keys = []
        for key, value in remaining_tasks.items():
            if value is not None:
                print(f'Got {key}')
            else:
                keys.append(key)
    if any(remaining_tasks):
        print(f'Didn\'t get results in time for {len(remaining_tasks.keys())} tasks')
        
        
"""
"""
timeit(lambda: sync_client_test(), number=30)
timeit(lambda: async_client_test(), number=30)
timeit(lambda: socket_client_test(), number=30)
"""