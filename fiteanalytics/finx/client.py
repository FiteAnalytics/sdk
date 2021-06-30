#! Python
"""
Author: Jake Mathai, Dick Mule
Purpose: Client classes for exposing the FinX API endpoints
"""
import os
import json
import asyncio
import requests
import pandas as pd

from lru import LRU
from uuid import uuid4
from gc import collect
from time import sleep
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


class _BaseClient:
    """
    Client base class with LRU caching

    Default LRU cache architecture = LRU(100000) {
        "{security_id}security_reference": LRU(3) {
            "{reference_parameters_1}": reference_output_1,
            "{reference_parameters_2}": reference_output_2,
            "{reference_parameters_3}": reference_output_3
        },
        "{security_id}security_analytics": LRU(3) {
            "{analytics_parameters_1}": analytics_output_1,
            "{analytics_parameters_2}": analytics_output_2,
            "{analytics_parameters_3}": analytics_output_3
        },
        "{security_id}security_cash_flows": LRU(1) {
            "{cash_flows_parameters}": cash_flows_output
        },
        ...
        "list_api_functions": LRU(1) {
            "NONE": api_functions
        }
    }
    """
    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint, or
        FINX_API_KEY and FINX_API_ENDPOINT environment variables

        :keyword finx_api_key: string, optional
        :keyword finx_api_endpoint: string, optional
        :keyword cache_size: int, maximum number of objects to hold in first layer of LRU cache. Default 100000, optional
        :keyword cache_method_size: dict, map available method names to maximum allowed objects for each functions's LRU
                  cache in the second layer of the cache. Default:
                  {'security_reference': 3, 'security_analytics': 3, 'security_cash_flows': 1}, optional
        """
        self.__api_key = kwargs.get('finx_api_key') or os.environ.get('FINX_API_KEY')
        if self.__api_key is None:
            raise Exception('API key not found - please include the keyword argument '
                            'finx_api_key or set the environment variable FINX_API_KEY')
        self.__api_url = kwargs.get('finx_api_endpoint') or os.environ.get('FINX_API_ENDPOINT') or DEFAULT_API_URL
        self.cache_size = kwargs.get('cache_size') or 100000
        self.cache = LRU(self.cache_size)
        self._session = requests.session() if kwargs.get('session', True) else None
        self._executor = ThreadPoolExecutor() if kwargs.get('executor', True) else None
        self.cache_method_size = kwargs.get('cache_method_size') or {
            'security_reference': 3,
            'security_analytics': 3,
            'security_cash_flows': 1
        }

    def close_session(self):
        if self._session is not None:
            self._session.close()

    def get_api_key(self):
        return self.__api_key

    def get_api_url(self):
        return self.__api_url

    def clear_cache(self):
        self.cache.clear()
        collect()
        return None

    def check_cache(self, api_method, security_id=None, params=None):
        if params is None:
            params = dict()
        cache_key = f'{security_id or ""}{api_method}'
        params_key = ','.join([
            f'{key}:{params[key]}' for key in sorted(params.keys())
            if key not in ['security_id', 'api_method', 'input_file', 'output_file', 'blocking']
        ])
        if len(params_key) == 0:
            params_key = 'NONE'
        cached_value = self.cache.get(cache_key)
        if cached_value is None:
            self.cache[cache_key] = LRU(1) if security_id is None else LRU(self.cache_method_size.get(api_method, 1))
            self.cache[cache_key][params_key] = None
        else:
            cached_value = cached_value.get(params_key)
        return cached_value, cache_key, params_key


class _SyncFinXClient(_BaseClient):
    """
    FinX synchronous HTTP client
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__api_key = self.get_api_key()
        self.__api_url = self.get_api_url()

    def _dispatch(self, api_method, **kwargs):
        assert self._session is not None
        request_body = {
            'finx_api_key': self.__api_key,
            'api_method': api_method,
        }
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method'
            })
        if api_method == 'security_analytics':
            request_body['use_kalotay_analytics'] = False
        cached_response, cache_key, params_key = self.check_cache(api_method, kwargs.get('security_id'), request_body)
        if cached_response is not None:
            print('Found in cache')
            return cached_response
        request_body['finx_api_key'] = self.__api_key
        data = self._session.post(self.__api_url, data=request_body).json()
        error = data.get('error')
        if error is not None:
            print(f'API returned error: {error}')
            return data
        self.cache[cache_key][params_key] = data
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

    def get_curve(self, curve_name, currency, start_date, end_date=None, **kwargs):
        """
        Yield curve function

       :param curve_name: string
       :param currency: string
       :param start_date: string as YYYY-MM-DD
       :param end_date: string as YYYY-MM-DD. Default None, optional
       """
        return self._dispatch(
            'get_curve',
            curve_name=curve_name,
            currency=currency,
            start_date=start_date,
            end_date=end_date or start_date,
            **kwargs)

    def _dispatch_batch(self, api_method, security_params, **kwargs):
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
    """
    FinX asynchronous HTTP client
    """
    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint,
        or FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        super().__init__(**kwargs, session=False, executor=False)
        self.__api_key = self.get_api_key()
        self.__api_url = self.get_api_url()

    async def close_session(self):
        if self._session is not None:
            await self._session.close()

    async def _dispatch(self, api_method, **kwargs):
        """
        Abstract request dispatch function
        """
        if self._session is None:
            self._session = ClientSession()
        request_body = {
            'finx_api_key': self.__api_key,
            'api_method': api_method,
        }
        if any(kwargs):
            request_body.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method' and value is not None
            })
        if api_method == 'security_analytics':
            request_body['use_kalotay_analytics'] = False
        cached_response, cache_key, params_key = self.check_cache(api_method, kwargs.get('security_id'), request_body)
        if cached_response is not None:
            print('Request found in cache')
            return cached_response
        async with self._session.post(self.__api_url, data=request_body) as response:
            data = await response.json()
            error = data.get('error')
            if error is not None:
                print(f'API returned error: {error}')
                return response
            self.cache[cache_key][params_key] = data
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
        assert api_method != 'list_api_functions' and type(security_params) is list and len(security_params) < 100
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


class _BaseSocketClient(_BaseClient):
    """
    Websocket client base class
    """
    def __init__(self, **kwargs):
        """
        Client constructor - supports keywords finx_api_key and finx_api_endpoint,
        or FINX_API_KEY and FINX_API_ENDPOINT environment variables
        """
        super().__init__(**kwargs, session=False)
        self.__api_key = self.get_api_key()
        self.__api_url = self.get_api_url()
        self.__auth_payload = json.dumps({'finx_api_key': self.__api_key})
        self.__ws_url = f'{"wss" if kwargs.get("ssl", True) else "ws"}://{urlparse(self.__api_url).netloc}/ws/api/'
        self.is_authenticated = False
        self.blocking = kwargs.get('blocking', True)
        self._init_socket()

    def authenticate(self):
        print('Authenticating...')
        self._socket.send(self.__auth_payload)

    def _run_socket(self, url, on_message, on_error):
        """
        Spawn websocket connection in daemon thread
        """
        try:
            self._socket = _WebSocket(
                url,
                on_open=lambda s: self.authenticate(),
                on_message=on_message,
                on_error=on_error,
                on_close=lambda s: print('Socket closed'))
            self._socket_thread = Thread(
                target=self._socket.run_forever,
                daemon=True,
                kwargs={'skip_utf8_validation': True, 'sslopt': {'check_hostname': False}})
            self._socket_thread.start()
        except Exception as e:
            raise Exception(f'Failed to connect to {url}: {e}')

    def _init_socket(self):
        """
        Define websocket connection with callbacks and run as daemon process
        """
        self.is_authenticated = False

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
                if type(data) is not list and (type(data) is not dict or data.get('progress') is not None):
                    print(message)
                    return None
                cache_keys = message.get('cache_key')
                if cache_keys is None:
                    return None
                if type(data) is list and type(data[0]) is dict:
                    for key in cache_keys:
                        self.cache[key[1]][key[2]] = next(
                            (item for item in data if item.get('security_id') in key[1]), None)
                else:
                    for key in cache_keys:
                        self.cache[key[1]][key[2]] = data
            except:
                print(f'Socket on_message error: {format_exc()}')
            return None

        def on_error(socket, error):
            print(f'Socket on_error: {error}')
            if not socket.is_connected():
                self._init_socket()

        print(f'Connecting to {self.__ws_url}')
        self._run_socket(self.__ws_url, on_message, on_error)

    def close_session(self):
        if self._socket.is_connected():
            self._socket.close()

    def _listen_for_results(self, cache_keys, callback=None, **kwargs):
        """
        Process listening for result of a request and optionally executing callback on the result. If blocking == False,
        runs as an async threadpool process
        """
        try:
            results = []
            remaining_keys = cache_keys
            while len(remaining_keys) != 0:
                sleep(0.01)
                remaining_results = [self.cache.get(key[1], dict()).get(key[2], None) for key in remaining_keys]
                remaining_keys = [remaining_keys[index] for index, value in enumerate(remaining_results) if
                                  value is None]
                results += [x for x in remaining_results if x is not None]
            file_results = [value for value in results
                            if type(value) is dict and value.get('filename') is not None]
            if any(file_results):
                print('Downloading results...')
                file_df = pd.read_csv(StringIO(
                    requests.get(
                        f'{self.__api_url}batch-download/',
                        params={'filename': file_results[0][1].get('filename')}
                    ).content.decode('utf-8')
                ))
                file_cache_results = dict(zip(
                    file_df['security_id'].map(
                        lambda x: next((pair[0] for pair in file_results if x in pair[0]), None)),
                    file_df.to_dict(orient='records')))
                results.update(file_cache_results)
                print('Updating cache with file data...')
                for key, value in file_cache_results.items():
                    self.cache[key] = value
            output_file = kwargs.get('output_file')
            if output_file is not None and len(results) > 0 and type(results[0]) in [list, dict]:
                print(f'Writing data to {output_file}')
                pd.DataFrame(results).to_csv(output_file, index=False)
            if callable(callback):
                return callback(results, **kwargs, cache_keys=cache_keys)
            return results if len(results) > 1 else results[0] if len(results) > 0 else results
        except:
            print(f'Failed to find result/execute callback: {format_exc()}')

    def _parse_batch_input(self, batch_input, base_cache_payload):
        """
        Extract batch input data from either direct input or csv/txt file. Sends to server as a file if large
        """
        print('Parsing batch input...')
        batch_input_df = (pd.read_csv if type(batch_input) is str else pd.DataFrame)(batch_input)
        batch_input_df['cache_keys'] = [
            self.check_cache(
                base_cache_payload['api_method'],
                security_input.get('security_id'),
                {**base_cache_payload, **security_input}
            ) for security_input in batch_input_df.to_dict(orient='records')
        ]
        batch_input_df['cached_responses'] = batch_input_df['cache_keys'].str[0]
        cache_keys = batch_input_df['cache_keys'].tolist()
        cached_responses = batch_input_df.loc[
            batch_input_df['cached_responses'].notnull()]['cached_responses'].tolist()
        outstanding_requests = batch_input_df.loc[batch_input_df['cached_responses'].isnull()].to_dict(orient='records')
        return cache_keys, cached_responses, outstanding_requests

    def _upload_batch_file(self, batch_input):
        """
        Send batch input file to server for later retrieval in dispatch on server side
        """
        print('Uploading batch file...')
        filename = f'{uuid4()}.csv'
        if type(batch_input) in [pd.DataFrame, pd.Series]:
            batch_input.to_csv(filename, index=False)
        elif type(batch_input) is list:
            if type(batch_input[0]) in [dict, list]:
                pd.DataFrame(batch_input).to_csv(filename, index=False)
            elif type(batch_input[0]) is str:
                with open(filename, 'w+') as file:
                    file.write('\n'.join(batch_input))
        file = open(filename, 'rb')
        response = requests.post(  # Upload file to server and record filename
            f'{self.__api_url}batch-upload/',
            data={'finx_api_key': self.__api_key},
            files={'file': file}).json()
        print(response)
        file.close()
        os.remove(filename)
        if response['failed']:
            raise Exception(f'Failed to upload file: {response["message"]}')
        print('Batch file uploaded')
        return response['filename']

    def _dispatch(self, api_method, **kwargs):
        """
        Abstract API dispatch function
        """
        if not self._socket.is_connected():
            print('Socket is not connected - reconnecting...')
            self._init_socket()
        if not self.is_authenticated:
            print('Awaiting authentication...')
            for i in range(5000):
                sleep(0.001)
                if self.is_authenticated:
                    break
            if not self.is_authenticated:
                raise Exception('Client not authenticated')
        payload = {'api_method': api_method}
        callback = kwargs.pop('callback', None)
        if any(kwargs):
            payload.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method'
            })
        if 'security_analytics' in api_method:
            payload['use_kalotay_analytics'] = False
        if kwargs.pop('is_batch', False):
            batch_input = kwargs.pop('batch_input')
            base_cache_payload = kwargs.copy()
            base_cache_payload['api_method'] = api_method
            if 'security_analytics' in api_method:
                base_cache_payload['use_kalotay_analytics'] = False
            cache_keys, cached_responses, outstanding_requests = self._parse_batch_input(
                batch_input,
                base_cache_payload)
            total_requests = len(cached_responses) + len(outstanding_requests)
            if len(cached_responses) == total_requests:
                print(f'All {total_requests} requests found in cache')
                if callable(callback):
                    return callback(cached_responses, **kwargs, cache_keys=cache_keys)
                return cached_responses
            print(f'{len(cached_responses)} out of {total_requests} requests found in cache')
            if getsizeof(outstanding_requests) > 1e6:
                payload['batch_input'] = self._upload_batch_file(outstanding_requests)
            else:
                payload['batch_input'] = outstanding_requests
            payload['api_method'] = f'batch_{api_method}'
        else:
            cache_keys = self.check_cache(api_method, payload.get('security_id'), payload)
            if cache_keys[0] is not None:
                print('Request found in cache')
                if callable(callback):
                    return callback(cache_keys[0], **kwargs, cache_keys=cache_keys)
                return cache_keys[0]
            cache_keys = [cache_keys]
        payload['cache_key'] = cache_keys if type(payload.get('batch_input')) is not str else []
        self._socket.send(json.dumps(payload))
        blocking = kwargs.get('blocking', self.blocking)
        if blocking:
            return self._listen_for_results(cache_keys, callback, **kwargs)
        if callable(callback):
            self._executor.submit(self._listen_for_results, cache_keys, callback, **kwargs)
        return cache_keys

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

                        def callback(result, **kwargs): ...

                  If True or not null, uses the generic callback function _batch_callback() defined above.
                  Default None, optional
        :keyword blocking: bool - block main thread until result arrives and return the value. Default is object's
                  configured default, optional
        """
        batch_input = security_params or input_file
        assert batch_method != 'list_api_functions' and batch_input is not None
        return self._dispatch(
            batch_method,
            batch_input=batch_input,
            **kwargs,
            input_file=input_file,
            output_file=output_file,
            is_batch=True)


class _SocketFinXClient(_BaseSocketClient, _SyncFinXClient):
    """
    FinX websocket client
    """
    def batch_coverage_check(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Check coverage for batch of securities
        """
        return self._dispatch_batch('coverage_check', security_params, input_file, output_file, **kwargs)

    def batch_security_reference(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Get security reference data for batch of securities
        """
        return self._dispatch_batch('security_reference', security_params, input_file, output_file, **kwargs)

    def batch_security_analytics(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Get security analytics for batch of securities
        """
        return self._dispatch_batch('security_analytics', security_params, input_file, output_file, **kwargs)

    def batch_security_cash_flows(self, security_params=None, input_file=None, output_file=None, **kwargs):
        """
        Get security cash flows for batch of securities
        """
        return self._dispatch_batch('security_cash_flows', security_params, input_file, output_file, **kwargs)


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
