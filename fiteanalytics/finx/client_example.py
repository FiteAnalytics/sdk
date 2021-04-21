"""
client_example.py
"""

import json
from fiteanalytics.finx.client import FinXClient

# Initialize socket client
# Credentials fetched from environment variables
finx = FinXClient('socket')

# Get API methods
print('\n*********** API Methods ***********')
api_methods = finx.get_api_methods(block=True)
print(json.dumps(api_methods, indent=4))

security_id = 'USQ98418AH10'
as_of_date = '2020-09-14'

# Get security reference data
print('\n*********** Security Reference Data ***********')
reference_data = finx.get_security_reference_data(
    security_id, 
    as_of_date=as_of_date,
    block=True)
print(json.dumps(reference_data, indent=4))

# Get security analytics
print('\n*********** Security Analytics ***********')
analytics = finx.get_security_analytics(
    security_id, 
    as_of_date=as_of_date, 
    price=100,
    block=True)
print(json.dumps(analytics, indent=4))

# Get projected cash flows
print('\n*********** Security Cash Flows ***********')
cash_flows = finx.get_security_cash_flows(
    security_id, 
    as_of_date=as_of_date, 
    price=100,
    block=True)
print(json.dumps(cash_flows, indent=4))

# Batch get security reference data
print('\n*********** Batch Get Security Reference Data ***********')
batch_reference_data = finx.batch_security_reference(
    [
        {
            'security_id': 'USQ98418AH10',
            'as_of_date': '2020-09-14'
        },
        {
            'security_id': '3133XXP50',
            'as_of_date': '2020-09-14'
        }
    ],
    block=True
)
print(json.dumps(batch_reference_data, indent=4))
