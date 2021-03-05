#! Python

import sys
from os import path
sys.path.append(path.join(path.dirname(__file__), '..'))
from finx_api.finx import FinX

finx = FinX('finx_api/finx_config.yml')

print('\n*********** API methods ***********')
api_methods = finx.get_api_methods()
print(api_methods)

security_id = 'USQ98418AH10'
as_of_date = '2020-09-14'

print('\n*********** Security Reference Data ***********')
reference_data = finx.get_security_reference_data(security_id, as_of_date)
print(reference_data)

print('\n*********** Security Analytics ***********')
analytics = finx.get_security_analytics(security_id, as_of_date, price=100)
print(analytics)

print('\n*********** Security Cash Flows ***********')
cash_flows = finx.get_security_cash_flows(security_id, as_of_date, price=100)
print(cash_flows)
