"""
client_example.py
"""

import json
from client import FinXClient

# Initialize socket client
# Credentials fetched from environment variables
finx = FinXClient('socket')

# Get API methods
print('\n*********** API Methods ***********')
api_methods = finx.list_api_functions(block=True)
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

# Batch get security reference data
print('\n*********** Batch Coverage Check ***********')
batch_reference_data = finx.batch_coverage_check(
    [
        {'security_id': 'USQ98418AH10'},
        {'security_id': '3133XXP50'},
        {'security_id': 'ARARGE03E105'},
        {'security_id': 'ARARGE03E121'},
        {'security_id': 'ARARGE03E121'},
        {'security_id': 'ARARGE03E121'},
        {'security_id': 'ARARGE03E147'},
        {'security_id': 'ARARGE03G621'},
        {'security_id': 'ARARGE3202H4'},
        {'security_id': 'ARARGE320283'},
        {'security_id': 'ARARGE3203R1'},
        {'security_id': 'ARARGE3208K5'},
        {'security_id': 'ARARGE3208S8'},
        {'security_id': 'ARARGE3208T6'},
        {'security_id': 'ARARGE3208U4'},
        {'security_id': 'ARARGE3208X8'},
        {'security_id': 'ARARGE3209H9'},
        {'security_id': 'ARARGE3209S6'},
        {'security_id': 'ARARGE3209T4'},
        {'security_id': 'ARARGE3209U2'},
        {'security_id': 'ARARGE3209Y4'}
    ]
)
print(json.dumps(batch_reference_data, indent=4))
