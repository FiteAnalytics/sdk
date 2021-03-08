import fs  from "fs";
import axios from "axios";
import yaml from "js-yaml";

function FinX(yaml_path=null, env_path=null) {
    var api_key = null,
        api_url = null;
    if (yaml_path != null) {
        const fileContents = fs.readFileSync(yaml_path, 'utf8'),
            config = yaml.load(fileContents);
        api_key = config['FINX_API_KEY'];
        api_url = config['FINX_API_ENDPOINT'];
    }
    else {
        if (env_path != null)
            try {
                require('dotenv').config({path: env_path});
            }
            catch(e) {
                console.log(`Could not load .env file at ${env_path}`);
            }
        api_key = process.env.FINX_API_KEY;
        api_url = process.env.FINX_API_ENDPOINT;
    }
    if (typeof api_key == 'undefined' || api_key == null)
        throw new Error('API key not found');
    if (typeof api_url == 'undefined' || api_url == null)
        api_url = 'https://sandbox.finx.io/api/';

    var request_body = {};

    async function dispatch() {
        const response = await axios.post(api_url, request_body);
        return response.data;
    }

    async function get_api_methods() {
        request_body = {
            finx_api_key: api_key,
            api_method: 'list_api_functions'
        };
        return await dispatch();
    }

    async function get_security_reference_data(security_id, as_of_date=null) {
        request_body = {
            finx_api_key: api_key,
            api_method: 'security_reference',
            security_id: security_id,
        };
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
        return await dispatch();
    }

    async function get_security_analytics(security_id,
                                          as_of_date=null,
                                          price=null,
                                          volatility=null,
                                          yield_shift=null,
                                          shock_in_bp=null,
                                          horizon_months=null,
                                          income_tax=null,
                                          cap_gain_short_tax=null,
                                          cap_gain_long_tax=null) {
        request_body = {
            finx_api_key: api_key,
            api_method: 'security_analytics',
            security_id: security_id
        };
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
        if (price != null)
            request_body['price'] = price;
        if (volatility != null)
            request_body['volatility'] = volatility;
        if (yield_shift != null)
            request_body['yield_shift'] = yield_shift;
        if (shock_in_bp != null)
            request_body['shock_in_bp'] = shock_in_bp;
        if (horizon_months != null)
            request_body['horizon_months'] = horizon_months;
        if (income_tax != null)
            request_body['income_tax'] = income_tax;
        if (cap_gain_short_tax != null)
            request_body['cap_gain_short_tax'] = cap_gain_short_tax;
        if (cap_gain_long_tax != null)
            request_body['cap_gain_long_tax'] = cap_gain_long_tax;
        return await dispatch();
    }

    async function get_security_cash_flows(security_id, as_of_date=null, price=null, shock_in_bp=null) {
        request_body = {
            finx_api_key: api_key,
            api_method: 'security_cash_flows',
            security_id: security_id
        };
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
        if (price != null)
            request_body['price'] = price;
        if (shock_in_bp != null)
            request_body['shock_in_bp'] = shock_in_bp;
        return await dispatch();
    }

    return {
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows
    }
}

export default FinX;
