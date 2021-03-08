#! Python
import sys
from os import path
sys.path.append(path.join(path.dirname(__file__), '..'))
from finx_api.finx import FinX

# Initialize client
finx = FinX(yaml_path='finx_api/finx_config.yml')

# Get API methods
print('\n*********** API methods ***********')
api_methods = finx.get_api_methods()
print(api_methods)

security_id = 'USQ98418AH10'
as_of_date = '2020-09-14'

# Get security reference data
print('\n*********** Security Reference Data ***********')
reference_data = finx.get_security_reference_data(security_id, as_of_date)
print(reference_data)

# Get security analytics
print('\n*********** Security Analytics ***********')
analytics = finx.get_security_analytics(security_id, as_of_date=as_of_date, price=100)
print(analytics)

# Get projected cash flows
print('\n*********** Security Cash Flows ***********')
cash_flows = finx.get_security_cash_flows(security_id, as_of_date=as_of_date, price=100)
print(cash_flows)
