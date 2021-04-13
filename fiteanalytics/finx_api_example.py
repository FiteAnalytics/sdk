#! Python
"""
finx_api_example.py
"""
import json
import sys

from fiteanalytics import finx_api


if __name__ == "__main__":
    """
    optional command line arguments:
    argv[0] = security_id
    argv[1] = as_of_date
    """

    # Initialize client
    finx_client = finx_api.FinX()

    # Get API methods
    print('\n*********** API Methods ***********')
    api_methods = finx_client.get_api_methods()
    print(json.dumps(api_methods, indent=4))

    # GET (OPTIONAL) COMMAND LINE ARGUMENTS
    security_id = sys.argv[1] if len(sys.argv) > 1 else 'USQ98418AH10'
    as_of_date = sys.argv[2] if len(sys.argv) > 2 else '2020-09-14'

    # Get security reference data
    print('\n*********** Security Reference Data ***********')
    reference_data = finx_client.get_security_reference_data(security_id, as_of_date)
    print(json.dumps(reference_data, indent=4))

    # Get security analytics
    print('\n*********** Security Analytics ***********')
    analytics = finx_client.get_security_analytics(security_id, as_of_date=as_of_date, price=100)
    print(json.dumps(analytics, indent=4))

    # Get projected cash flows
    print('\n*********** Security Cash Flows ***********')
    cash_flows = finx_client.get_security_cash_flows(security_id, as_of_date=as_of_date, price=100)
    print(json.dumps(cash_flows, indent=4))
