#! Python
"""
finx_api_example.py
"""
import json
from fiteanalytics.finx_api import FinX

# Initialize synchronous client with no arguments -
# checks environment variables for credentials
finx = FinX()

# Get API methods
print('\n*********** API Methods ***********')
api_methods = finx.get_api_methods()
print(json.dumps(api_methods, indent=4))

security_id = 'USQ98418AH10'
as_of_date = '2020-09-14'

# Get security reference data
print('\n*********** Security Reference Data ***********')
reference_data = finx.get_security_reference_data(
    security_id,
    as_of_date=as_of_date)
print(json.dumps(reference_data, indent=4))

# Get security analytics
print('\n*********** Security Analytics ***********')
analytics = finx.get_security_analytics(
    security_id,
    as_of_date=as_of_date,
    price=100)
print(json.dumps(analytics, indent=4))

# Get projected cash flows
print('\n*********** Security Cash Flows ***********')
cash_flows = finx.get_security_cash_flows(
    security_id,
    as_of_date=as_of_date,
    price=100)
print(json.dumps(cash_flows, indent=4))
