#! Python
"""
client.py
"""
import os
import json
import asyncio
import requests
import pandas as pd

from lru import LRU
from time import sleep
from uuid import uuid4
from gc import collect
from io import StringIO
from sys import getsizeof
from threading import Thread
from traceback import format_exc
from aiohttp import ClientSession
from urllib.parse import urlparse
from websocket import WebSocketApp, enableTrace
from concurrent.futures import ThreadPoolExecutor


enableTrace(False)

DEFAULT_API_URL = 'https://sandbox.finx.io/api/'


def _get_cache_key(params):
    return ','.join([f'{key}:{params[key]}' for key in sorted(params.keys())])


class _SyncFinXClient:

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint, or
        FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        self.__api_key = kwargs.get('finx_api_key') or os.environ.get('FINX_API_KEY')
        if self.__api_key is None:
            raise Exception('API key not found - please include the keyword argument '
                            'finx_api_key or set the environment variable FINX_API_KEY')
        self.__api_url = kwargs.get('finx_api_endpoint') or os.environ.get('FINX_API_ENDPOINT') or DEFAULT_API_URL
        self.cache_size = kwargs.get('cache_size') or 100
        self.cache = LRU(self.cache_size)
        self._session = requests.session() if kwargs.get('session', True) else None
        self._executor = ThreadPoolExecutor() if kwargs.get('executor', True) else None

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    def clear_cache(self):
        self.cache.clear()
        collect()
        return None

    def _dispatch(self, api_method, **kwargs):
        assert self._session is not None
        request_body = {
            'finx_api_key': self.__api_key,
            'api_method': api_method
        }
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        if api_method == 'security_analytics':
            request_body['use_kalotay_analytics'] = False
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

    def list_api_functions(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return self._dispatch('list_api_functions', **kwargs)

    def coverage_check(self, security_id, **kwargs):
        """
        Security coverage check

        :param security_id: string - ID of security of interest
        """
        return self._dispatch('coverage_check', security_id=security_id, **kwargs)

    def get_security_reference_data(self, security_id, **kwargs):
        """
        Security reference function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD. Default None, optional
        """
        return self._dispatch('security_reference', security_id=security_id, **kwargs)

    def get_security_analytics(self, security_id, **kwargs):
        """
        Security analytics function

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
        """
        return self._dispatch('security_analytics', security_id=security_id, **kwargs)

    def get_security_cash_flows(self, security_id, **kwargs):
        """
        Security cash flows function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD. Default None, optional
        :keyword price: float. Default 100.0, optional
        :keyword shock_in_bp: int. Default None, optional
        """
        return self._dispatch('security_cash_flows', security_id=security_id, **kwargs)

    async def _dispatch_batch(self, api_method, security_params, **kwargs):
        """
        Abstract batch request dispatch function. Issues a request for each input
        """
        assert self._executor is not None \
            and api_method != 'list_api_functions' \
            and type(security_params) is list \
            and len(security_params) < 100
        tasks = [self._executor.submit(self._dispatch, api_method, **security_param, **kwargs)
                 for security_param in security_params]
        return [task.result() for task in tasks]

    def batch_coverage_check(self, security_params, **kwargs):
        """
        Check coverage for batch of securities
        :param security_params: List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return self._dispatch_batch('coverage_check', security_params, **kwargs)

    def batch_security_reference(self, security_params, **kwargs):
        """
        Get security reference data for batch of securities
        :param security_params: List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return self._dispatch_batch('security_reference', security_params, **kwargs)

    def batch_security_analytics(self, security_params, **kwargs):
        """
        Get security analytics for batch of securities
        :param security_params: List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return self._dispatch_batch('security_analytics', security_params, **kwargs)

    def batch_security_cash_flows(self, security_params, **kwargs):
        """
        Get security cash flows for batch of securities
        :param security_params: List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return self._dispatch_batch('security_cash_flows', security_params, **kwargs)


class _AsyncFinXClient(_SyncFinXClient):

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint,
        or FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        super().__init__(**kwargs, session=False, executor=False)
        self.__api_key = self.get_api_key()
        self.__api_url = self.get_api_url()

    async def _dispatch(self, api_method, **kwargs):
        """
        Abstract request dispatch function
        """
        if self._session is None:
            self._session = ClientSession()
        request_body = {
            'finx_api_key': self.__api_key,
            'api_method': api_method
        }
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        if api_method == 'security_analytics':
            request_body['use_kalotay_analytics'] = False
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

    async def list_api_functions(self, **kwargs):
        """
        List API methods with parameter specifications
        """
        return await self._dispatch('list_api_functions', **kwargs)

    async def coverage_check(self, security_id, **kwargs):
        """
        Security coverage check

        :param security_id: string - ID of security of interest
        """
        return await self._dispatch('coverage_check', security_id=security_id, **kwargs)

    async def get_security_reference_data(self, security_id, **kwargs):
        """
        Security reference function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD. Default None, optional
        """
        return await self._dispatch('security_reference', security_id=security_id, **kwargs)

    async def get_security_analytics(self, security_id, **kwargs):
        """
        Security analytics function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD. Default None, optional
        :keyword price: float. Default None, optional
        :keyword volatility: float. Default None, optional
        :keyword yield_shift: int. Default None, optional
        :keyword shock_in_bp: int. Default None, optional
        :keyword horizon_months: uint. Default None, optional
        :keyword income_tax: float. Default None, optional
        :keyword cap_gain_short_tax: float. Default None, optional
        :keyword cap_gain_long_tax: float. Default None, optional
        """
        return await self._dispatch('security_analytics', security_id=security_id, **kwargs)

    async def get_security_cash_flows(self, security_id, **kwargs):
        """
        Security cash flows function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD. Default None, optional
        :keyword price: float. Default None, optional
        :keyword shock_in_bp: int. Default None, optional
        """
        return await self._dispatch('security_cash_flows', security_id=security_id, **kwargs)

    async def _dispatch_batch(self, api_method, security_params, **kwargs):
        """
        Abstract batch request dispatch function. Issues a request for each input
        """
        assert api_method != 'list_api_functions' \
            and type(security_params) is list \
            and len(security_params) < 100
        try:
            asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        tasks = [self._dispatch(api_method, **security_param, **kwargs) for security_param in security_params]
        return await asyncio.gather(*tasks)

    async def batch_coverage_check(self, security_params, **kwargs):
        """
        Check coverage for batch of securities
        :param security_params: (list) List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return await self._dispatch_batch('coverage_check', security_params, **kwargs)

    async def batch_security_reference(self, security_params, **kwargs):
        """
        Get security reference data for batch of securities
        :param security_params: (list) List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return await self._dispatch_batch('security_reference', security_params, **kwargs)

    async def batch_security_analytics(self, security_params, **kwargs):
        """
        Get security analytics for batch of securities
        :param security_params: (list) List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return await self._dispatch_batch('security_analytics', security_params, **kwargs)

    async def batch_security_cash_flows(self, security_params, **kwargs):
        """
        Get security cash flows for batch of securities
        :param security_params: (list) List of dicts containing the security_id and keyword arguments for each security
                function invocation
        """
        return await self._dispatch_batch('security_cash_flows', security_params, **kwargs)


class _WebSocket(WebSocketApp):

    def is_connected(self):
        return self.sock is not None and self.sock.connected


class _SocketFinXClient(_SyncFinXClient):

    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint,
        or FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        super().__init__(**kwargs, session=False)
        self.__api_key = super().get_api_key()
        self.__api_url = super().get_api_url()
        self.ssl = kwargs.get('ssl', False)
        self.is_authenticated = False
        self.block = kwargs.get('block') or True
        self._init_socket()

    def _run_socket(self, url, on_open, on_message, on_error):
        """
        Spawn websocket connection in daemon thread
        """
        try:
            self._socket = _WebSocket(
                url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=lambda s: print('Socket closed'))
            self._socket_thread = Thread(
                target=self._socket.run_forever,
                daemon=True,
                kwargs={'skip_utf8_validation': True})
            self._socket_thread.start()
        except Exception as e:
            raise Exception(f'Failed to connect to {url}: {e}')

    def _init_socket(self):
        """
        Define websocket connection with callbacks and run as daemon process
        """
        def on_open(socket):
            print('Socket connected. Authenticating...')
            socket.send(json.dumps({'finx_api_key': self.__api_key}))
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
                    data = message.get('data', message.get('message', {}))
                if type(data) is list or (type(data) is dict and data.get('progress') is None):
                    self.cache[message['cache_key']] = data
                else:
                    print(message)
            except Exception as e:
                print(f'Socket on_message error: {e}')
            return None

        def on_error(socket, error):
            print(f'Socket on_error: {error}')
            if not socket.is_connected():
                self._init_socket()

        url = f'{"wss" if self.ssl else "ws"}://{urlparse(self.__api_url).netloc}/ws/api/'
        print(f'Connecting to {url}')
        self._run_socket(url, on_open, on_message, on_error)

    def _listen_for_result(self, cache_key, callback=None, **kwargs):
        """
        Async process run in threadpool to listen for result of a request and execute callback upon arrival. Only used
        if callback specified in a function call
        """
        try:
            result = None
            while result is None:
                sleep(.001)
                result = self.cache.get(cache_key)
            if callable(callback):
                return callback(result, **kwargs, cache_key=cache_key)
            return result
        except:
            print(f'Failed to find result/execute callback: {format_exc()}')

    def _dispatch(self, api_method, **kwargs):
        """
        Abstract method dispatch function
        """
        if not self._socket.is_connected():
            self._init_socket()
        if not self.is_authenticated:
            print('Awaiting authentication...')
            i = 5000
            while not self.is_authenticated and i >= 1:
                sleep(.001)
                i -= 1
            if not self.is_authenticated:
                raise Exception('Client not authenticated')
        payload = {'api_method': api_method}
        callback = kwargs.pop('callback', None)
        if any(kwargs):
            payload.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        if api_method == 'security_analytics':
            payload['use_kalotay_analytics'] = False
        cache_key = _get_cache_key(payload)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            print('Found in cache')
            if callable(callback):
                callback(cached_response, **kwargs)
            return cached_response
        payload['cache_key'] = cache_key
        self._socket.send(json.dumps(payload))
        block = kwargs.get('block') or self.block
        if callable(callback):
            if block:
                self._listen_for_result(cache_key, callback, **kwargs)
            else:
                self._executor.submit(self._listen_for_result, cache_key, callback, **kwargs)
        elif block:
            return self._listen_for_result(cache_key, **kwargs)
        return cache_key

    def _upload_batch_file(self, security_params):
        """
        Send batch input file to server for later retrieval during dispatch on server side
        """
        filename = f'{uuid4()}.csv'
        if type(security_params) in [pd.DataFrame, pd.Series]:
            security_params.to_csv(filename, index=False)
        elif type(security_params) is list:
            if type(security_params[0]) in [dict, list]:
                pd.DataFrame(security_params).to_csv(filename, index=False)
            elif type(security_params[0]) is str:
                with open(filename, 'w+') as file:
                    file.write('\n'.join(security_params))
        file = open(filename, 'rb')
        response = requests.post(  # Upload file to server and record filename
            self.__api_url + 'batch-upload/',
            data={'finx_api_key': self.__api_key},
            files={'file': file}).json()
        print(response)
        file.close()
        os.remove(filename)
        if response['failed']:
            raise Exception(f'Failed to upload file: {response["message"]}')
        print('File uploaded')
        return response['filename']

    def _get_batch_input(self, security_params=None, input_file=None):
        """
        Extract batch input data from either direct input or csv/txt file. Sends to server as a file if large
        """
        print('Parsing input...')
        if security_params is None and input_file is not None:
            security_params = pd.read_csv(input_file).head(200).to_dict(orient='records')
        assert security_params is not None and any(security_params)
        if getsizeof(security_params) > 10e6:  # Do file I/O if large batch
            print('Uploading file...')
            return self._upload_batch_file(security_params)
        return security_params

    def _batch_callback(self, result, **kwargs):
        """
        Generic callback function called upon batch completion. Fetches file result from server if result contains the
        filename, else gets the result directly. Writes result to file if output file specified, else caches raw results
        """
        print('Getting results...')
        if type(result) is dict and result.get('filename'):  # Download results
            print('Downloading results...')
            data = pd.read_csv(StringIO(
                requests.get(
                    self.__api_url + 'batch-download/',
                    params={'filename': result.get('filename')}).content.decode('utf-8')))
        else:  # Get results directly
            data = pd.DataFrame(result)
        output_file = kwargs.get('output_file')
        if output_file is not None:
            self.cache[kwargs['cache_key']] = output_file
            print(f'Writing data to {output_file}')
            data.to_csv(output_file, index=False)
        else:
            self.cache[kwargs['cache_key']] = data.to_dict(orient='records')
        print('Batch results available!')
        return None

    def _dispatch_batch(self, batch_method, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Abstract batch request dispatch function. Issues a single request containing all inputs. Must either give the
        inputs directly in security_params or specify absolute path to input_file. Specify the parameters & keywords and
        invoke using the defined batch functions below

        :param security_params: list - List of dicts containing the security_id and keyword arguments for each security
                function invocation. Default None, optional
        :param input_file: string - path to csv/txt file containing parameters for each security, row-wise.
                Default None, optional
        :param output_file: string - path to csv/txt file to output results to, default None, optional
        :keyword callback: callable - function to execute on result once received. Function signature should be:

                        def callback(result, **kwargs):

                  If keyword value specified is True or not null, uses the generic callback function _batch_callback()
                  defined above. Default None, optional
        :keyword block: bool - block main thread until result arrives and return the value. Default False, optional
        """
        assert batch_method != 'list_api_functions' and (security_params is not None or input_file is not None)
        callback = kwargs.get('callback')
        if callback and not callable(callback):
            kwargs['callback'] = self._batch_callback
        return self._dispatch(
            batch_method,
            security_params=self._get_batch_input(security_params, input_file),
            **kwargs,
            input_file=input_file,
            output_file=output_file)

    def batch_coverage_check(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Check coverage for batch of securities
        """
        return self._dispatch_batch('batch_coverage_check', security_params, input_file, output_file, **kwargs)

    def batch_security_reference(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Get security reference data for batch of securities
        """
        return self._dispatch_batch('batch_security_reference', security_params, input_file, output_file, **kwargs)

    def batch_security_analytics(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Get security analytics for batch of securities
        """
        return self._dispatch_batch('batch_security_analytics', security_params, input_file, output_file, **kwargs)

    def batch_security_cash_flows(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Get security cash flows for batch of securities
        """
        return self._dispatch_batch('batch_security_cash_flows', security_params, input_file, output_file, **kwargs)


def FinXClient(kind='sync', **kwargs):
    """
    Unified interface to spawn FinX client. Use keyword "kind" to specify the type of client
    :param kind: string - 'socket' for websocket client, 'async' for async client. Default 'sync', optional
    """
    if kind == 'socket':
        return _SocketFinXClient(**kwargs)
    if kind == 'async':
        return _AsyncFinXClient(**kwargs)
    return _SyncFinXClient(**kwargs)
