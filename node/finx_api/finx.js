/*
finx.js
 */
import axios from "axios";

function FinX(kwargs={}) {
    
    const DEFAULT_API_URL = 'https://sandbox.finx.io/api/';
    
    let api_key = kwargs['finx_api_key'],
        api_url = kwargs['finx_api_endpoint'];
    if (api_key == null) {
        api_key = process.env.FINX_API_KEY;
        api_url = process.env.FINX_API_ENDPOINT;
    }
    if (api_key == null)
        throw new Error('API key not found');
    if (api_url == null)
        api_url = DEFAULT_API_URL;
    let max_cache_size = kwargs['max_cache_size'];
    if (max_cache_size == null)
        max_cache_size = 100;
    let cache = new Map();
    
    /*
    Add non-null keyword args to request body, prevent overriding of api_method and finx_api_key, and send request
     */
    
    const dispatch = async(request_body, kwargs={}) => {
        if (Object.keys(kwargs).length !== 0) {
            for (const key in kwargs) {
                if (kwargs.hasOwnProperty(key) && key !== 'finx_api_key' && key !== 'api_method') {
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
    
    const batch = async(api_method, security_args={}) => {
        console.assert(typeof api_method == 'function' && api_method !== get_api_methods);
        let tasks = [];
        if (api_method === get_security_reference_data) {
            for (const security_id in security_args) {
                if (security_args.hasOwnProperty(security_id))
                    tasks.push(api_method(security_id, security_args[security_id]['as_of_date']));
            }
        }
        else {
            for (const security_id in security_args) {
                if (security_args.hasOwnProperty(security_id))
                    tasks.push(api_method, security_args[security_id]);
            }
        }
        return await axios.all(tasks);
    };

    return {
        get_api_key: () => api_key,
        get_api_url: () => api_url,
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows,
        batch: batch
    }
}


function FinXSocket(kwargs={}) {
    
    const DEFAULT_API_URL = 'https://sandbox.finx.io/api/';
    
    let api_key = kwargs['finx_api_key'],
        api_url = kwargs['finx_api_endpoint'];
    if (api_key == null) {
        api_key = process.env.FINX_API_KEY;
        api_url = process.env.FINX_API_ENDPOINT;
    }
    if (api_key == null)
        throw new Error('API key not found');
    if (api_url == null)
        api_url = DEFAULT_API_URL;
    let max_cache_size = kwargs['max_cache_size'];
    if (max_cache_size == null)
        max_cache_size = 100;
    let cache = new Map();
    
    let socket;
    
    const get_cache_key = (params) => {
        return Object.keys(params).sort().map(key => `${key}:${params[key]}`).join('_');
    };
    
    const clear_cache = () => { cache = new Map(); };
    
    const onopen = () => {
        const params = {'finx_api_key': api_key};
        console.log(`Sending ${params}`);
        socket.send(JSON.stringify(params));
    };
    
    const onmessage = (message) => {
        message = JSON.parse(message)['data'];
        console.log(data);
        if (message['is_authenticated']) {
            console.log('Successfully authenticated');
            return;
        }
        const error = message['error'];
        if (error) {
            console.log(`API returned error: ${error}`);
            return;
        }
        if (cache.length >= max_cache_size)
            cache.delete(cache.keys()[0]);
        cache.set(get_cache_key(message['input_params']), message['data']);
    };
    
    const onclose = () => console.log('Socket connection closed');
    
    let endpoint = (new URL(api_url)).host + '/ws/api/';
    try {
        let url = `ws://${endpoint}`;
        console.log(`Connecting to ${url}`);
        socket = new WebSocket(url);
    }
    catch(e) {
        console.log(`Could not connect to WS endpoint: ${e}; trying WS...`)
        let url = `wss://${endpoint}`;
        console.log(`Connecting to ${url}`);
        socket = new WebSocket(url);
    }
    socket.onopen = onopen;
    socket.onmessage = onmessage;
    socket.onclose = onclose;
    
    const await_result = async(cache_key, callback, kwargs={}) => {
        let result = null;
        while (result == null)
            result = cache[cache_key];
        await callback(result, kwargs);
    };
    
    /*
    Add non-null keyword args to request body, prevent overriding of api_method and finx_api_key, and send request
     */
    const dispatch = async(payload, kwargs={}) => {
        const callback = kwargs['callback'];
        delete kwargs['callback'];
        if (Object.keys(kwargs).length !== 0) {
            for (const key in kwargs) {
                if (kwargs.hasOwnProperty(key) && key !== 'finx_api_key' && key !== 'api_method') {
                    const value = kwargs[key];
                    if (value != null)
                        payload[key] = value;
                }
            }
        }
        const cache_key = get_cache_key(payload);
        const cached_response = cache[cache_key];
        if (cached_response != null) {
            console.log('Found in cache');
            if (typeof callback === 'function') {
                if (callback.constructor.name === 'AsyncFunction')
                    await callback(cached_response, kwargs);
                else
                    callback(cached_response, kwargs);
            }
            return cached_response
        }
        socket.send(JSON.stringify(payload));
        if (typeof callback === 'function')
            await await_result(cache_key, callback, kwargs);
        return cache_key;
    };

    /*
    List API methods with parameter specifications
     */
    const get_api_methods = async() => {
        return await dispatch({api_method: 'list_api_functions'});
    };

    /*
    Security reference function

    :param security_id: string
    :param as_of_date: string as YYYY-MM-DD (optional)
     */
    const get_security_reference_data = async(security_id, as_of_date=null) => {
        let payload = {
            api_method: 'security_reference',
            security_id: security_id,
        };
        if (as_of_date != null)
            payload['as_of_date'] = as_of_date;
        return await dispatch(payload)
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
            api_method: 'security_cash_flows',
            security_id: security_id
        }, kwargs)
    };
    
    const batch = async(api_method, security_args={}) => {
        console.assert(typeof api_method == 'function' && api_method !== get_api_methods);
        let tasks = [];
        if (api_method === get_security_reference_data) {
            for (const security_id in security_args) {
                if (security_args.hasOwnProperty(security_id))
                    tasks.push(api_method(security_id, security_args[security_id]['as_of_date']));
            }
        }
        else {
            for (const security_id in security_args) {
                if (security_args.hasOwnProperty(security_id))
                    tasks.push(api_method(security_id, security_args[security_id]));
            }
        }
        return tasks;
    };

    return {
        get_api_key: () => api_key,
        get_api_url: () => api_url,
        clear_cache: clear_cache,
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows,
        batch: batch
    }
}


export default FinX;
