import axios from "axios";
import { load } from "js-yaml";
import { readFileSync }  from "fs";

function FinX(kwargs={}) {
    let api_key = null,
        api_url = null;
    const yaml_path = kwargs['yaml_path'];
    if (yaml_path != null) {
        const config = load(readFileSync(yaml_path, 'utf8'));
        api_key = config['FINX_API_KEY'];
        api_url = config['FINX_API_ENDPOINT'];
    }
    else {
        const env_path = kwargs['env_path'];
        if (env_path != null)
            try {
                require('dotenv').config({path: env_path});
            }
            catch(e) {
                console.log(`Could not load .env file at ${env_path}: ${e}`);
            }
        api_key = process.env.FINX_API_KEY;
        api_url = process.env.FINX_API_ENDPOINT;
    }
    if (api_key == null)
        throw new Error('API key not found');
    if (api_url == null)
        api_url = 'https://sandbox.finx.io/api/';

    /*
    Add non-null keyword args to request body, prevent overriding of api_method and finx_api_key, and send request
     */
    const dispatch = async(request_body, kwargs={}) => {
        if (Object.keys(kwargs).length !== 0) {
            for (const key in kwargs) {
                if (kwargs.hasOwnProperty(key) && key !== 'api_method' && key !== 'finx_api_key') {
                    const value = kwargs[key];
                    if (value != null)
                        request_body[key] = value;
                }
            }
        }
        return (await axios.post(api_url, request_body)).data
    };

    /*
    List API methods with parameter specifications
     */
    const get_api_methods = async() => {
        return await dispatch({
            finx_api_key: api_key,
            api_method: 'list_api_functions'
        })
    };

    /*
    Security reference function

    :param security_id: string
    :param as_of_date: string as YYYY-MM-DD (optional)
     */
    const get_security_reference_data = async(security_id, as_of_date=null) => {
        let request_body = {
            finx_api_key: api_key,
            api_method: 'security_reference',
            security_id: security_id,
        };
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
        return await dispatch(request_body)
    };

    /*
    Security analytics function

    :param security_id: string (required)
    :keyword as_of_date: string as YYYY-MM-DD (optional)
    :keyword price: float (optional)
    :keyword volatility: float (optional)
    :keyword yield_shift: int (basis points, optional)
    :keyword shock_in_bp: int (basis points, optional)
    :keyword horizon_months: uint (optional)
    :keyword income_tax: float (optional)
    :keyword cap_gain_short_tax: float (optional)
    :keyword cap_gain_long_tax: float (optional)
     */
    const get_security_analytics = async(security_id, kwargs={}) => {
        return await dispatch({
            finx_api_key: api_key,
            api_method: 'security_analytics',
            security_id: security_id
        }, kwargs)
    };

    /*
    Security cash flows function

    :param security_id: string
    :keyword as_of_date: string as YYYY-MM-DD (optional)
    :keyword price: float (optional)
    :keyword shock_in_bp: int (optional)
     */
    const get_security_cash_flows = async(security_id, kwargs={}) => {
        return await dispatch({
            finx_api_key: api_key,
            api_method: 'security_cash_flows',
            security_id: security_id
        }, kwargs)
    };

    return {
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows
    }
}

export default FinX;
