from urllib.parse import urlencode

import requests

import ciscotropowebapi

from app import config


def webhook_process(request, webhook_url):
    """
     POST'd data from Tropo WebAPI on inbound voice/sms call

     It is possible to create a similar script and host on Tropo.
     Beware, some caveats exist in Tropo's environment. Eg:
     https://www.tropo.com/docs/coding-tips/parsing-json-python

     """
    # Parse data passed in by Tropo
    tropo_session = ciscotropowebapi.Session(request.data.decode())

    # Create empty tropo response
    tropo_response = ciscotropowebapi.Tropo()

    # Check to see if this is a request to send a message
    if hasattr(tropo_session, 'parameters'):

        number_to_call = tropo_session.parameters['numberToDial']
        print("send_sms request to %s. Message %s" % (number_to_call, tropo_session.parameters['msg']))

        # add a + if necessary
        if not number_to_call.startswith('+'):
            number_to_call = '+' + number_to_call

        # Send SMS: https://www.tropo.com/docs/webapi/quickstarts/sending-text-messages
        # tropo_response.call(to=number_to_call, network="SMS")
        # tropo_response.say(tropo_session.msg)

        # Better yet, use the message "shortcut"
        # https://www.tropo.com/docs/webapi/quickstarts/mixing-text-voice-single-app/using-message-shortcut
        tropo_response.message(tropo_session.parameters['msg'], number_to_call, network="SMS")
    # Inbound Voice Call
    elif tropo_session.from_['network'] is 'VOICE':
        print("Voice call from %s. Redirecting to %s" %
              (tropo_session.from_['id'], config.CUSTOMER_SERVICE_REDIRECT_DN) )
        # Send voice calls to the contact center DN
        tropo_response.redirect(config.CUSTOMER_SERVICE_REDIRECT_DN)
    # Inbound SMS
    elif hasattr(tropo_session, 'initialText'):
        if config.SPARK_TOKEN:
            # Avoid circular imports, only import right before use
            from app import spark
            # post message to Spark room
            spark_message = spark.customer_room_message_send(tropo_session.from_['id'],
                                                             text=tropo_session.initialText,
                                                             webhook_url=webhook_url)

            # if there was an error, notify caller
            if not spark_message:
                tropo_response.say("There was a problem receiving your request, please try again later.")
        else:
            print("Inbound SMS received from %s: Message: %s" % (tropo_session.from_['id'], tropo_session.initialText))
    else:
        raise InvalidRequestError("Invalid request")

    # Return response to Tropo
    return tropo_response.RenderJson()


class InvalidRequestError(Exception):
    pass


def send_sms(destination_number, text_message):
    """
    Simple function to send customer_id a SMS by triggering a Tropo application based on TROPO_KEY
    https://www.tropo.com/docs/webapi/quickstarts/sending-text-messages
    
    Beware of international SMS regulations: 
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