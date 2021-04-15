/*
finx.js
 */
import axios from "axios";
import WebSocket from 'ws';
import LRU from "lru-cache";

const DEFAULT_API_URL = 'https://sandbox.finx.io/api/';

var lru_options = {
    max: Infinity,
    length: function (n, key) { return n * 2 + key.length },
    maxAge: Infinity
};

const sleep = async duration => await new Promise(r => setTimeout(r, duration));

const _get_cache_key = params => Object.keys(params).sort().map(key => `${key}:${params[key]}`).join('_');

async function dispatch() {}

const _FinX = (kwargs={}) => {
    
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
    lru_options.max = max_cache_size;
    let cache = new LRU(lru_options);
    
    const clear_cache = () => {cache = new LRU(lru_options);};
    
    /*
    Add non-null keyword args to request body, prevent overriding of api_method and finx_api_key, and send request
     */
    dispatch = async(request_body, kwargs={}) => {
        if (Object.keys(kwargs).length !== 0) {
            for (const key in kwargs) {
                if (kwargs.hasOwnProperty(key) && key !== 'finx_api_key' && key !== 'api_method') {
                    const value = kwargs[key];
                    if (value != null)
                        request_body[key] = value;
                }
            }
        }
        const cache_key = _get_cache_key(request_body);
        const cached_response = cache.get(cache_key);
        if (cached_response != null) {
            console.log('Found in cache');
            return cached_response
        }
        request_body['finx_api_key'] = api_key;
        let data = (await axios.post(api_url, request_body)).data;
        let error = data['error'];
        if (error != null) {
            console.log(`API returned error: ${error}`);
            data = error;
        }
        cache.set(cache_key, data);
        return data
    };

    /*
    List API methods with parameter specifications
     */
    const get_api_methods = async() => await dispatch({api_method: 'list_api_functions'});

    /*
    Security reference function

    :param security_id: string
    :param as_of_date: string as YYYY-MM-DD (optional)
     */
    const get_security_reference_data = async(security_id, kwargs={}) => {
        let request_body = {
            api_method: 'security_reference',
            security_id: security_id,
        };
        const as_of_date = kwargs['as_of_date'];
        if (as_of_date != null)
            request_body['as_of_date'] = as_of_date;
        return await dispatch(request_body, kwargs)
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
        console.assert(
            typeof api_method == 'function'
            && api_method !== get_api_methods
            && Object.keys(security_args).length <= 100);
        let tasks = [];
        for (const security_id in security_args) {
            if (security_args.hasOwnProperty(security_id))
                tasks.push(api_method(security_id, security_args[security_id]));
        }
        return await axios.all(tasks);
    };

    return {
        get_api_key: () => api_key,
        get_api_url: () => api_url,
        cache: cache,
        clear_cache: clear_cache,
        get_api_methods: get_api_methods,
        get_security_reference_data: get_security_reference_data,
        get_security_analytics: get_security_analytics,
        get_security_cash_flows: get_security_cash_flows,
        batch: batch
    }
};


const _FinXSocket = (kwargs={}) => {
    
    let finx = _FinX(kwargs);
    finx.is_authenticated = false;
    let socket;
    
    const onopen = () => {
        console.log('Socket connected. Authenticating...');
        socket.send(JSON.stringify({'finx_api_key': finx.get_api_key()}));
    };
    
    const onmessage = (message) => {
        try {
            message = JSON.parse(message['data']);
            if (message['is_authenticated']) {
                console.log('Successfully authenticated');
                finx.is_authenticated = true;
                return;
            }
            let data;
            const error = message['error'];
            if (error) {
                console.log(`API returned error: ${error}`);
                data = error;
            }
            else
                data = message['data'];
            finx.cache.set(message['cache_key'], data);
        }
        catch(e) {
            console.log(`Socket on_message error: ${e}`);
        }
    };
    
    let protocol = kwargs['ssl'] === true ? 'wss' : 'ws';
    let endpoint = (new URL(finx.get_api_url())).host + '/ws/api/';
    let url = `${protocol}://${endpoint}`;
    console.log(`Connecting to ${url}`);
    try {
        socket = new WebSocket(url);
        socket.onopen = onopen;
        socket.onmessage = onmessage;
        socket.onclose = () => console.log('Socket connection closed');
    }
    catch(e) {
        throw new Error(`Failed to connect: ${e}`);
    }
    
    const let_result_arrive = async(cache_key, callback, kwargs={}) => {
        try {
            let result = null;
            while (result == null) {
                await sleep(.001);
                result = finx.cache.get(cache_key);
            }
            if (typeof callback === 'function') {
                if (callback.constructor.name === 'AsyncFunction')
                    await callback(result, kwargs);
                else
                    callback(result, kwargs);
            }
        }
        catch(e) {
            console.log(`Failed to await result/execute callback: ${e}`)
        }
    };
    
    /*
    Add non-null keyword args to request body, prevent overriding of api_method and finx_api_key, and send request
     */
    dispatch = async(payload, kwargs={}) => {
        if (!finx.is_authenticated) {
            let i = 5000;
            console.log('Awaiting authentication...');
            while (!finx.is_authenticated) {
                await sleep(1);
                --i;
            }
            if (!finx.is_authenticated)
                throw new Error('Client not authenticated');
        }
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
        const cache_key = _get_cache_key(payload);
        const cached_response = finx.cache.get(cache_key);
        if (cached_response != null) {
            console.log('Found in cache:', cached_response);
            if (typeof callback === 'function') {
                if (callback.constructor.name === 'AsyncFunction')
                    await callback(cached_response, kwargs);
                else
                    callback(cached_response, kwargs);
            }
            return cached_response
        }
        payload['cache_key'] = cache_key;
        socket.send(JSON.stringify(payload));
        if (typeof callback === 'function')
            await let_result_arrive(cache_key, callback, kwargs);
        return cache_key;
    };
    
    finx.batch = async(api_method, security_args={}, kwargs={}) => {
        console.assert(
            typeof api_method == 'function'
            && api_method !== finx.get_api_methods
            && Object.keys(security_args).length <= 100);
        let tasks = [];
        for (const security_id in security_args) {
            if (security_args.hasOwnProperty(security_id))
                security_args[security_id] = {...security_args[security_id], ...kwargs};
                tasks.push(api_method(security_id, security_args[security_id]));
        }
        return tasks;
    };
    return finx;
};

const Finx = (kind='async', kwargs={}) => kind === 'socket' ? _FinXSocket(kwargs) : _FinX(kwargs);

export default Finx;
