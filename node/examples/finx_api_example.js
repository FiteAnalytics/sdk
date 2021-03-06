/*
finx_api_example.js
 */
import FinX from "../finx_api/finx.js";

// Initialize client with YAML configuration
let finx = FinX({yaml_path: '../../finx_config.yml'});

// Get API methods
finx.get_api_methods().then(data => {
    console.log('\n*********** API Methods ***********');
    console.log(data);
});

const security_id = 'USQ98418AH10', as_of_date = '2020-09-14';

// Get security reference data
finx.get_security_reference_data(security_id, as_of_date).then(data => {
    console.log('\n*********** Security Reference Data ***********');
    console.log(data);
});

// Get security analytics
finx.get_security_analytics(security_id, {as_of_date: as_of_date, price: 100}).then(data => {
    console.log('\n*********** Security Analytics ***********');
    console.log(data);
});

// Get projected cash flows
finx.get_security_cash_flows(security_id, {as_of_date: as_of_date, price: 100}).then(data => {
    console.log('\n*********** Security Cash Flows ***********');
    console.log(data);
});

// Batch security reference
finx.batch(
    finx.get_security_reference_data,
    {
        'USQ98418AH10': {
            'as_of_date': '2020-09-14'
        },
        '3133XXP50': {
            'as_of_date': '2020-09-14'
        }
    }
).then(responses => {
    console.log('\n*********** Batch ***********');
    console.log(responses)
});