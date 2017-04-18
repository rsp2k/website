from urllib.parse import urlencode

import requests

from app import config

def send_sms(customer_id, message):
    """
    Simple function to send customer_id a SMS via Tropo
    https://www.tropo.com/docs/webapi/quickstarts/sending-text-messages
    """

    query_string = {'action':'create',
                    'token': config.TROPO_KEY,
                    'numberToDial':customer_id,
                    'message':message,
                   }
    url = 'https://api.tropo.com/1.0/sessions?%s' % urlencode(query_string)
    call = requests.get(url,headers={'content-type':'application/x-www-form-urlencoded'})
    return call
