import axios from "axios";

function FinX(api_key=null, env_path=null) {
    const api_url = 'https://sandbox.finx.io/api/';
    var request_body = {};
    if (api_key == null) {
        if (env_path != null)
            require('dotenv').config({path: env_path});
        api_key = process.env.API_KEY;
    }
    console.assert(api_key != null);

    const dispatch = () => axios.post(api_url, request_body).then(response => response.data);

    function get_api_methods() {
        request_body = {
            finx_api_key: api_key,
            api_method: 'list_api_functions'
        };
        return dispatch();
    }

    function get_security_reference_data(security_id, as_of_date=null) {
        request_body = {
            finx_api_key: api_key,
            api_method: 'security_reference',
            security_id: security_id,
		};
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
		return dispatch();
    }

    const security_analytics_args = ['security_id', 'as_of_date', 'price', 'volatility', 'yield_shift', 'shock_in_bp',
        'horizon_months', 'income_tax', 'cap_gain_short_tax', 'cap_gain_long_tax'];
    function get_security_analytics(security_id,
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
        };
        for (let i = 0; i !== security_analytics_args.length; ++i) {
            if (arguments[i] != null)
                request_body[security_analytics_args[i]] = arguments[i];
		}
        return dispatch();
    }

    const cash_flows_args = ['security_id', 'as_of_date', 'price', 'shock_in_bp'];
    function get_security_cash_flows(security_id, as_of_date=null, price=null, shock_in_bp=null) {
        request_body = {
			finx_api_key: api_key,
			api_method: 'security_cash_flows',
		};
        for (let i = 0; i !== cash_flows_args.length; ++i) {
            if (arguments[i] != null)
                request_body[cash_flows_args[i]] = arguments[i];
		}
		return dispatch();
    }

    return {
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows
    }
}

export default FinX;
