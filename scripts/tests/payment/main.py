
from flask import Flask, url_for, redirect, request

from suds.client import Client
import sys
sys.path.append('helpers')
from initial import get_secrets_config

app = Flask(__name__)

MMERCHANT_ID = '99a59392-249d-11e6-bd81-000c295eb8fc'  # Required
ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'  # Required
# amount = 1000  # Amount will be based on Toman  Required
# description = u'توضیحات تراکنش تستی'  # Required
# email = 'user@userurl.ir'  # Optional
# mobile = '09123456789'  # Optional

(secrets, Config)=get_secrets_config()

@app.route('/request/')
def send_request():
    client = Client(ZARINPAL_WEBSERVICE)
    result = client.service.PaymentRequest(MMERCHANT_ID,
                                           amount,
                                           description,
                                           email,
                                           mobile,
                                           str(url_for('verify', _external=True)))
    if result.Status == 100:
        return redirect('https://www.zarinpal.com/pg/StartPay/' + result.Authority)
    else:
        return 'Error'


@app.route('/verify/', methods=['GET', 'POST'])
def verify():
    client = Client(ZARINPAL_WEBSERVICE)
    if request.args.get('Status') == 'OK':
        
        result = client.service.PaymentVerification(MMERCHANT_ID,
                                                    request.args['Authority'],
                                                    amount)
        print(result)
        if result.Status == 100:
            return 'Transaction success. RefID: ' + str(result.RefID)
        elif result.Status == 101:
            return 'Transaction submitted : ' + str(result.Status)
        else:
            return 'Transaction failed. Status: ' + str(result.Status)
    else:
        return 'Transaction failed or canceled by user'


if __name__ == '__main__':
    app.run(debug=False)