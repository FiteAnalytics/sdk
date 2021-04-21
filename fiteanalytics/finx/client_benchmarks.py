"""
client_benchmarks.py
"""
import time
import asyncio
from timeit import timeit
from asgiref.sync import AsyncToSync

from finx.client import FinXClient

BATCH_INPUTS = [
    {
        'security_id': '9127962F5',
        'as_of_date': '2021-03-24',
        'foo': 'bar'
    },
    {
        'security_id': 'USQ98418AH10',
        'as_of_date': '2020-09-14'
    },
    {
        'security_id': '912796B24',
        'as_of_date': '2021-04-01'
    },
    {
        'security_id': '912796F61',
        'as_of_date': '2021-04-01'
    }
]


def sync_client_test():
    finx = FinXClient()
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    finx.list_api_functions()
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    finx.get_security_analytics('9127962F5', as_of_date='2021-03-24')
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24')
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    finx.batch_security_analytics(BATCH_INPUTS)
    finx._session.close()


@AsyncToSync
async def async_client_test():
    finx = FinXClient('async')
    tasks = []
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    tasks.append(finx.list_api_functions())
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    tasks.append(finx.get_security_analytics('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    tasks.append(finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    tasks.append(finx.batch_security_analytics(BATCH_INPUTS))
    await asyncio.gather(*tasks)
    await finx._session.close()


def socket_client_test():
    finx = FinXClient('socket', block=False)
    keys = []
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    keys.append(finx.list_api_functions())
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    keys.append(finx.get_security_analytics('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    keys.append(finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    keys.append(finx.batch_security_analytics(input_file='/Users/jakemathai/Desktop/coverage.csv', output_file='/Users/jakemathai/Desktop/analytics_output.csv', callback=True))
    remaining_tasks = {key: finx.cache.get(key) for key in keys}
    keys = [key for key, value in remaining_tasks.items() if value is None]
    while any(remaining_tasks):
        time.sleep(0.001)
        remaining_tasks = {key: finx.cache.get(key) for key in keys}
        keys = [key for key, value in remaining_tasks.items() if value is None]
    if any(remaining_tasks):
        print(f'Didn\'t get results in time for {len(remaining_tasks.keys())} tasks')


timeit(lambda: sync_client_test(), number=1)
timeit(lambda: async_client_test(), number=1)
timeit(lambda: socket_client_test(), number=1)
