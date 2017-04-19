from urllib.parse import urlencode

import requests

from app import config


def send_sms(destination_number, text_message):
    """
    Simple function to send customer_id a SMS via Tropo
    https://www.tropo.com/docs/webapi/quickstarts/sending-text-messages
    Doesn't support international, beware of international SMS regulations: 
    https://www.tropo.com/docs/scripting/international-features/international-dialing-sms
    """

    # Our tropo script adds the +
    if destination_number.startswith("+"):
        destination_number = destination_number[1:]

    # Customer ID must start with one
    if not destination_number.startswith("1"):
        destination_number = "1" + destination_number

    if len(destination_number) < 11:
        raise DestinationNumberError("Destination Number not enough digits")

    query_string = {'action':'create',
                    'token':config.TROPO_KEY,
                    'numberToDial':destination_number,
                    'msg':text_message,
                   }

    url = 'https://api.tropo.com/1.0/sessions?%s' % urlencode(query_string)
    call = requests.get(url,headers={'content-type':'application/x-www-form-urlencoded'})
    return call


class DestinationNumberError(Exception):
    pass