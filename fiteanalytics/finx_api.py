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
from requests import session
from threading import Thread
from traceback import format_exc
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
        Client constructor - supports keywords finx_api_key and finx_api_endpoint, or
        FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        self.__api_key = kwargs.get('finx_api_key')
        self.__api_url = kwargs.get('finx_api_endpoint')
        if self.__api_key is None:
            self.__api_key = os.environ.get('FINX_API_KEY')
            self.__api_url = os.environ.get('FINX_API_ENDPOINT')
        if self.__api_key is None:
            raise Exception('API key not found - please include the keyword argument '
                            'finx_api_key or set the environment variable FINX_API_KEY')
        if self.__api_url is None:
            self.__api_url = DEFAULT_API_URL
        self.max_cache_size = kwargs.get('max_cache_size')
        if self.max_cache_size is None:
            self.max_cache_size = 100
        self.cache = LRU(self.max_cache_size)
        self._session = session() if kwargs.get('session') else None
        self._executor = ThreadPoolExecutor() if kwargs.get('executor') else None

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
        request_body['finx_api_key'] = self.__api_key
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
        :param security_args: Dict mapping security_id (string) to a dict of key word arguments
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
        Client constructor - supports keywords finx_api_key and finx_api_endpoint,
        or FINX_API_KEY and FINX_API_ENDPOINT environment variables
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
        :param security_args: Dict mapping security_id (string) to a dict of key word arguments
        """
        assert function != self.get_api_methods
        assert type(security_args) is dict
        assert len(security_args) < 100
        try:
            asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        tasks = [function(security_id=security_id, **kwargs)
                 for security_id, kwargs in security_args.items()]
        return await asyncio.gather(*tasks)


class _FinXSocket(_FinX):

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint,
        or FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        super().__init__(**kwargs, session=False)
        self.__api_key = super().get_api_key()
        self.__api_url = super().get_api_url()
        self.is_authenticated = False

        def on_open(socket):
            print('Socket connected. Authenticating...')
            self._socket.send(json.dumps({'finx_api_key': self.__api_key}))
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
                    data = error
                else:
                    data = message['data']
                self.cache[message['cache_key']] = data
            except Exception as e:
                print(f'Socket on_message error: {e}')
            return None

        protocol = 'wss' if kwargs.get('ssl') else 'ws'
        endpoint = urlparse(self.__api_url).netloc + '/ws/api/'
        url = f'{protocol}://{endpoint}'
        print(f'Connecting to {url}')
        try:
            self._socket = WebSocketApp(
                url,
                on_open=on_open,
                on_message=on_message,
                on_close=lambda socket: print('Socket closed'))
        except Exception as e:
            raise Exception(f'Failed to connect: {e}')
        self._socket_thread = Thread(
            target=self._socket.run_forever,
            kwargs={'ping_interval': 60},
            daemon=True)
        self._socket_thread.start()

    def _let_result_arrive(self, cache_key, callback, **kwargs):
        try:
            result = None
            while result is None:
                result = self.cache.get(cache_key)
            callback(result, **kwargs)
        except:
            print(f'Failed to await result/execute callback: {format_exc()}')

    def _dispatch(self, payload, **kwargs):
        if not self.is_authenticated:
            i = 5000
            print('Awaiting authentication...')
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
        self._socket.send(json.dumps(payload))
        if callable(callback):
            self._executor.submit(self._let_result_arrive, cache_key, callback, **kwargs)
        return cache_key

    def batch(self, function, security_args, **kwargs):
        """
        Invoke function for batch of securities
        :param function: Client member function to invoke for each security
        :param security_args: Dict mapping security_id (string) to a dict of key word arguments
        :keyword callback: function to invoke on each corresponding result when received
        """
        assert function != self.get_api_methods \
                and type(security_args) is dict \
                and len(security_args) < 100
        return [function(security_id, **_security_args, **kwargs)
                for security_id, _security_args in security_args.items()]


def FinX(kind='sync', **kwargs):
    """
    Unified interface to spawn FinX client. Use keyword "kind" to specify the type of client
    :keyword kind: (string) - 'socket' for websocket client, 'async' for async client, default sync client
    """
    if kind == 'socket':
        return _FinXSocket(**kwargs)
    if kind == 'async':
        return _AsyncFinx(**kwargs)
    return _FinX(**kwargs)
