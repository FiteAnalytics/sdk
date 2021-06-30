"""
client_benchmarks.py
"""
import asyncio
from timeit import timeit
from asgiref.sync import AsyncToSync

from client import FinXClient

BATCH_INPUTS = [
    {
        'security_id': '9127962F5',
        'as_of_date': '2021-03-24',
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
    print(finx.list_api_functions())
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    print(finx.get_security_analytics('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    print(finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    print(finx.batch_security_analytics(BATCH_INPUTS))
    finx.close_session()


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
    print(await asyncio.gather(*tasks))
    await finx.close_session()


def socket_client_test():
    finx = FinXClient('socket', blocking=True)
    keys = []
    print('\n' + '*'*20 + 'GET API METHODS' + '*'*20 + '\n')
    keys.append(finx.list_api_functions())
    print('\n' + '*'*20 + 'GET SECURITY ANALYTICS' + '*'*20 + '\n')
    keys.append(finx.get_security_analytics('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'GET SECURITY CASH FLOWS' + '*'*20 + '\n')
    keys.append(finx.get_security_cash_flows('9127962F5', as_of_date='2021-03-24'))
    print('\n' + '*'*20 + 'BATCH SECURITY ANALYTICS' + '*'*20 + '\n')
    keys.append(finx.batch_security_analytics(BATCH_INPUTS))


timeit(lambda: sync_client_test(), number=1)
timeit(lambda: async_client_test(), number=1)
timeit(lambda: socket_client_test(), number=1)
