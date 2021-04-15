import time
import asyncio
from timeit import timeit
from asgiref.sync import AsyncToSync
from fiteanalytics.finx.client import FinXClient


def sync_client_test():
    finx = FinXClient()
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
    finx = FinXClient('async')
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
    finx = FinXClient('socket')
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

    def get_keys(_remaining_tasks):
        _keys = []
        for key, value in remaining_tasks.items():
            if value is not None:
                print(f'Got {key}')
            else:
                _keys.append(key)
        return _keys

    keys = get_keys(remaining_tasks)
    while any(remaining_tasks) and i >= 1:
        time.sleep(0.001)
        i -= 1
        remaining_tasks = {key: finx.cache.get(key) for key in keys}
        keys = get_keys(remaining_tasks)
    if any(remaining_tasks):
        print(f'Didn\'t get results in time for {len(remaining_tasks.keys())} tasks')


timeit(lambda: sync_client_test(), number=30)
timeit(lambda: async_client_test(), number=30)
timeit(lambda: socket_client_test(), number=30)
