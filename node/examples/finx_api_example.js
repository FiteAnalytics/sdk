/*
finx_api_example.js
 */
import FinX from "../finx_api.js";

let use_async = false;

let finx = FinX(use_async ? 'async' : 'socket');
let result;

async function run() {
    result = await finx.get_api_methods({
        callback: async(result, kwargs={}) => console.log('API METHODS:', result)
    });
    if (use_async)
        console.log('API METHODS:', result);
    let security_id = 'USQ98418AH10';
    let as_of_date = '2020-09-14';
    result = await finx.get_security_reference_data(
        security_id,
        {
            as_of_date: as_of_date,
            callback: async(result, kwargs={}) => console.log('SECURITY REFERENCE:', result)
        }
    );
    if (use_async)
        console.log('SECURITY REFERENCE:', result);
    result = await finx.get_security_analytics(
        security_id,
        {
            as_of_date: as_of_date,
            price: 100,
            callback: async(result, kwargs={}) => console.log('SECURITY ANALYTICS:', result)
        }
    );
    if (use_async)
        console.log('SECURITY ANALYTICS:', result);
    result = await finx.get_security_cash_flows(
        security_id,
        {
            as_of_date: as_of_date,
            price: 100,
            callback: async(result, kwargs={}) => console.log('SECURITY CASH FLOWS:', result)
        }
    );
    if (use_async)
        console.log('SECURITY CASH FLOWS:', result);
    else
        finx.clear_cache();
    result = await finx.batch(
        finx.get_security_reference_data,
        {
            'USQ98418AH10': {
                as_of_date: '2020-09-14',
                callback: async(result, kwargs={}) => console.log('BATCH SECURITY REFERENCE 1:', result)
            },
            '3133XXP50': {
                as_of_date: '2020-09-14',
                callback: async(result, kwargs={}) => {
                    console.log('BATCH SECURITY REFERENCE 2:', result);
                    process.exit(0);
                }
            }
        }
    );
    if (use_async)
        console.log('BATCH SECURITY REFERENCE:', result);
    return 1;
}

run().then(x => console.log(x));
