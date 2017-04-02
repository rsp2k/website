# This contains our api; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/


# Python standard library modules
import os
from datetime import datetime
from urllib.parse import urlencode
import hashlib
import hmac

import logging

# Flask modules
from flask import Blueprint, render_template, redirect, url_for, request

# Third party modules
import requests

# Cisco specific modules
import ciscosparkapi
import ciscotropowebapi

# SmartSheet
if os.getenv('SMARTSHEET_TOKEN', None):
   import smartsheet

# Create blueprint object
api = Blueprint('api', __name__)

@api.route('/')
def index():
    """
    Our api index-page just shows a quick explanation from "templates/api.html"
    """
    return render_template('api.html')

@api.route('/tropo-webhook/', methods=['GET'])
def tropo_webhook_get():
    return render_template('tropo-webhook.html')

@api.route('/tropo-webhook/', methods=['POST'])
def tropo_webhook_post():
    """
    POST'd data from Tropo WebAPI on inbound voice/sms call

    It is possible to create a similar script and host on Tropo.
    Beware, some caveats exist in Tropo's environment. Eg:
    https://www.tropo.com/docs/coding-tips/parsing-json-python

    The hosted script would post received message data and calling phone number
    to the customer_room_message_send API endpoint.
    """
    # Parse data passed in by Tropo
    tropo_session = ciscotropowebapi.Session(request.data.decode())
    customer_id = tropo_session.from_['id']
    message = tropo_session.initialText

    # Create empty tropo response
    tropo_response = ciscotropowebapi.Tropo()

    # post messge to Spark room
    spark_message = customer_room_message_send(customer_id, text=message)

    # Acknowledge receipt/error of message
    if spark_message:
        # TODO Could add check to see if any agents on the rooms team are active and respond accordingly
        tropo_response.say("Thanks. An agent will get back to you as soon as possible. :)")
    else:
        tropo_response.say("There was a problem receiving your request, please try again later.")

    return tropo_response.RenderJson()

@api.route('/spark-webhook/', methods=['GET'])
def spark_webhook_get():
    return render_template('spark-webhook.html')

@api.route('/spark-webhook/', methods=['POST'])
def spark_webhook_post():
    """
    POST'd Data from Spark webhooks
    """

    if not request.json or not ('event' in request.json and 'data' in request.json):
        abort(400)

    if request.json['event'] is not 'message':
        abort(400)

    # Check for Spark Key defined
    webhook_key = os.getenv('SPARK_WEBHOOK_KEY', '')

    # only validate if key is defined
    if webhook_key:
        # Validate webhook - https://developer.ciscospark.com/blog/blog-details-8123.html
        hashed = hmac.new(webhook_key, request.data, hashlib.sha1)
        expected_signature = hashed.hexdigest()
        if expected_signature != request.headers.get('X-Spark-Signature'):
            abort(400)

    # extract message from JSON
    message = request.json

    # allow agents to privately exchange messages within context of the customer space
    # without sending a copy to the customer (agent whisper/notes)
    if message.mentionedPeople:
        return 'OK'

    # Get the room info from room id that was passed from webhook
    room = api.rooms.get(message.room.id)

    # customer id is room name
    customer_id = room.title

    send_customer_sms(customer_id, message.text)

    return 'OK'

@api.route('/customer_room_message_post/', methods=['GET'])
def customer_room_post_message_get():
    return render_template('customer-room-post-message.html')

@api.route('/customer_room_message_post/', methods=['POST'])
def customer_room_post_message_post():
    """
    API endpoint to customer_room_post_message

    """

    # make sure we have the data necessary to process the request
    if not request.json or not ('customer_id' in request.json and 'message' in request.json):
        abort(400)

    # initialize dictionary with customer id
    args = { 'customer_id': request.json['customer_id'] }

    # loop over allowed API parameters to be passed to function and add if found in JSON
    allowed_parameters = ['text', 'markdown', 'files']
    for parameter in allowed_parameters:
        if parameter in request.json:
            args.append(parameter, request.json[parameter])

    # pass customer id and upacked args to function
    message = customer_room_message_send(customer_id, **args)

    if not message:
       abort(500)

    return 'OK'

def customer_room_message_send(customer_id, **room_args):
    """
    Posts message to customer's Spark Room.
    Pass the customer #, the Spark Room ID will be looked up/created for you.
    """

    if 'text' not in room_args and 'markup' not in room_args and 'files' not in room_args:
           return None

    team_id = os.environ['SPARK_AGENT_TEAM_ID']
    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=os.environ['SPARK_TOKEN'])

    rooms = spark_api.rooms.list(teamId=team_id) # type='group')

    logging.info("Looking for %s's room" % customer_id)
    for room in rooms:
        logging.info("Checking room title %s" % room.title)
        if room.title[-10:] is customer_id[-10:]:
            break # found the customers room

    # If room is not found and break is never encountered, else block runs
    # http://book.pythontips.com/en/latest/for_-_else.html
    else:
        logging.info("Didn't find a room, creating a new one")
        # New customer
        room = customer_new_signup(customer_id, team_id)

    # post the message to spark room
    return spark_api.messages.create(roomId=room.id, **room_args)

def send_customer_sms(customer_id, message):
    """
    Simple function to send customer_id a SMS via Tropo
    https://www.tropo.com/docs/webapi/quickstarts/sending-text-messages
    """
    token = os.environ['TROPO_TOKEN']
    query_string = {'action':'create',
                    'token':token,
                    'numberToDial':customer_id,
                    'message':message,
                   }
    url = 'https://api.tropo.com/1.0/sessions?%s' % urlencode(query_string)
    call = requests.get(url,headers={'content-type':'application/x-www-form-urlencoded'})
    return call

def customer_room_webhook_create(target_url, room, resource, event, filter_, secret=None):
    """
    Create a webhook in room for resource on event filtered by filter_.
    Optionally set secret used to create signature
    """
    # we want notified anytime a message
    resource = "messages"
    # is created
    event = "created"
    # in the newly created room
    filter_ = "roomId=%s" % room.id

    # insecure example secret used to generate the payload signature
    secret = target_url + '12345'

    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=os.environ['SPARK_TOKEN'])
    webhook = spark_api.webhooks.create(room.title + 'messages created',
            target_url, resource, event, filter_, secret)

    return webhook


def customer_new_signup(customer_id, team_id):
    """
    Called when a new signup occurs
    * post message to customer via SMS and in spark room for agent to see
    * creates row in Smart Sheet

    NOTE: in a production environment these tasks would be offloaded to Celery
    or some other async job queue to keep users from waiting/isolate from errors
    """

    # Send message via tropo
    message = "Thanks for signing up! To get in touch, reply to this message or call this number during business hours."
    send_customer_sms(customer_id, message)

    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=os.environ['SPARK_TOKEN'])
    # create a new team room for the customer
    # http://ciscosparkapi.readthedocs.io/en/latest/user/api.html#ciscosparkapi.RoomsAPI.create
    room = spark_api.rooms.create(customer_id, teamId=team_id)

    # create webhook for new room
    # http://ciscosparkapi.readthedocs.io/en/latest/user/api.html#ciscosparkapi.WebhooksAPI.create

    # let flask build an external url based on SERVER_NAME
    target_url = url_for('.spark_webhook_post', _external=True)
    secret = None

    webhook = customer_room_webhook_create(target_url, room,
            "messages", "created", "roomId=%s" % room.id)

    smartsheet_log_signup(customer_id, datetime.now())

    return room

def smartsheet_log_signup(customer_id, signup_time):
    """
    Create row in smartsheet based on environment variables
    """

    if not os.getenv('SMARTSHEET_TOKEN', None):
        return None

    smartsheet_token = os.getenv('SMARTSHEET_TOKEN', None)
    signup_sheet_name = os.getenv('SMARTSHEET_SIGNUP_SHEET', None)

    if not smartsheet_token and signup_sheet_name:
        return None

    smartsheet_api = smartsheet.Smartsheet(smartsheet_token)
    action = smartsheet_api.Sheets.list_sheets(include_all=True)
    sheets = action.data
    for sheetInfo in sheets:
        if sheetInfo.name == signup_sheet_name:
            sheet = smartsheet_api.Sheets.get_sheet(sheetInfo.id)
            break

    else:
        print("Failed logging signup from %s. A smartsheet named %s wasn't found under token %s"
                % (customer_id, signup_sheet_name, smartsheet_token))

    columns = smartsheet_api.Sheets.get_columns(sheetInfo.id)
    row = smartsheet_api.models.Row()
    row.to_top = True
    row.cells.append({
            'column_id': cols['signup_time'],
            'value': signup_time,
            'strict': False
        },
        {
            'column_id': cols['phone'],
            'value': customer_id,
            'strict': False
        },
    )

    return smartsheet_api.Sheets.add_rows(sheetInfo.id, [row])

