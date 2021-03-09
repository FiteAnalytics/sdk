import fs  from "fs";
import axios from "axios";
import { load } from "js-yaml";

function FinX(kwargs={}) {
    let api_key = null,
        api_url = null;
    const yaml_path = kwargs['yaml_path'];
    if (yaml_path != null) {
        const fileContents = fs.readFileSync(yaml_path, 'utf8'),
            config = load(fileContents);
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

    const load_keyword_arguments = (request_body, kwargs) => {
        for (let key in kwargs) {
            if (kwargs.hasOwnProperty(key)) {
                let value = kwargs[key];
                if (value != null)
                    request_body[key] = value;
            }
        }
        return request_body
    };

    const dispatch = async request_body => (await axios.post(api_url, request_body)).data;

    const get_api_methods = async() => await dispatch({
        /*
        List API methods with parameter specifications
         */
        finx_api_key: api_key,
        api_method: 'list_api_functions'
    });

    const get_security_reference_data = async(security_id, as_of_date=null) => {
        /*
        Security reference function

        :param security_id: string
        :param as_of_date: string as YYYY-MM-DD (optional)
         */
        let request_body = {
            finx_api_key: api_key,
            api_method: 'security_reference',
            security_id: security_id,
        };
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
        return await dispatch(request_body);
    };

    const get_security_analytics = async(security_id, kwargs={}) => {
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
        const request_body = load_keyword_arguments({
            finx_api_key: api_key,
            api_method: 'security_analytics',
            security_id: security_id
        }, kwargs);
        return await dispatch(request_body);
    };

    const get_security_cash_flows = async(security_id, kwargs={}) => {
        /*
        Security cash flows function

        :param security_id: string
        :keyword as_of_date: string as YYYY-MM-DD (optional)
        :keyword price: float (optional)
        :keyword shock_in_bp: int (optional)
         */
        const request_body = load_keyword_arguments({
            finx_api_key: api_key,
            api_method: 'security_cash_flows',
            security_id: security_id
        }, kwargs);
        return await dispatch(request_body);
    };

    return {
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows
    }
}

export default FinX;
