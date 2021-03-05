import FinX from "../finx_api/finx.js";

let finx = FinX();

finx.get_api_methods().then(data => {
    console.log('\n*********** API methods ***********');
    console.log(data);
});

const security_id = 'USQ98418AH10', as_of_date = '2020-09-14';

finx.get_security_reference_data(security_id, as_of_date).then(data => {
    console.log('\n*********** Security Reference Data ***********');
    console.log(data);
});

finx.get_security_analytics(security_id, as_of_date).then(data => {
    console.log('\n*********** Security Analytics ***********');
    console.log(data);
});

finx.get_security_cash_flows(security_id, as_of_date).then(data => {
    console.log('\n*********** Security Cash Flows ***********');
    console.log(data);
});