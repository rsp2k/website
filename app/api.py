# This contains our api; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

from flask import Blueprint, render_template, redirect, url_for, request

from datetime import datetime

from urllib.parse import urlencode
import requests

from ciscosparkapi import CiscoSparkAPI
import app.tropo
import smartsheet

api = Blueprint('api', __name__)

@api.route('/')
def index():
    """
    Our api index-page just shows a quick explanation from "templates/api.html"
    """
    return render_template('api.html')

@api.route('/tropo-webhook', methods=['GET'])
def tropo_webhook_get():
    return 'Try POST?'


@api.route('/tropo-webhook', methods=['POST'])
def tropo_webhook():
    """
    POST'd data from Tropo WebAPI on inbound voice/sms call
    """

    s = tropo.Session(request.body)

    t = tropo.Tropo()
    if s.from_channel is 'VOICE':
        t.say(os.getenv('CS_VOICE_GREETING', "Transferring you now, please wait."))
        t.transfer({to: os.getenv('CS_VOICE_DN', '+18005551212')})
        return t.RenderJson()

    customer_id = s.fromaddress['id']
    message = s.initialText

    message_posted = customer_room_post_message(customer_id, text=message)
    if message_posted:
        t.say("We received your message and and agent will get back to you soon.")
    else:
        t.say("There was a problem recieving your request, please try again later.")

    return t.RenderJson()

@api.route('/spark-webhook', methods=['GET'])
def spark_webhook_get():
    return 'Try POST?'

@api.route('/spark-webhook', methods=['POST'])
def spark_webhook_post():
    """
    POST'd Data from Spark webhooks
    """

    if not request.json or not ('event' in request.json and 'data' in request.json):
        abort(400)

    if request.json['event'] is not 'message':
        abort(400)

    message = request.json

    # allow agents to privately excange messages within context of the customer space
    if message.mentionedPeople:
        return 'OK'

    # parse out customers phone number from room name
    room = api.rooms.get(message.room.id)
    customer_id = room.title

    send_customer_sms(customer_id, message)

    return 'OK'

@api.route('/customer-webhook', methods=['GET'])
def customer_webhook_get():
    return 'Try POST?'

@api.route('/customer-webhook', methods=['POST'])
def customer_webhook_post():
    """
    API endpoint to customer_room_post_message

    """
    if not request.json or not ('customer_id' in request.json and 'message' in request.json):
        abort(400)

    args = { 'customer_id': request.json['customer_id'] }
    if 'text' in request.json:
        args.append('text', request.json['text'])

    if 'files' in request.json:
        args.append('files', request.json['files'])

    # unpack args and pass to function
    message = customer_room_post_message(customer_id, **args)

    if not message:
       abort(500)

    return 'OK'

def customer_room_post_message(customer_id, **room_args):
    """
    Posts message to customer's Spark Room.
    Pass the customer #, the Spark Room ID will be looked up/created for you.
    """

    team_id = current_app.config['SPARK_AGENT_TEAM_ID']
    api = CiscoSparkAPI(access_token=current_app.config['SPARK_TOKEN'])

    rooms = api.rooms.list(teamId=team_id, type='group')

    for room in rooms:
        if room.title is customer_id:
            break # found the customers room

    # If room is not found and break is never encountered, else block runs
    # http://book.pythontips.com/en/latest/for_-_else.html
    else:
        # New customer
        room = customer_new_signup(customer_id, team_id)

    # post the message to spark room
    return api.messages.create(roomId=room.id, **room_args)

def send_customer_sms(customer_id, message):
    """
    Generic function to send customer_id message via SMS
    """
    token = os.getenv('TROPO_TOKEN', '')

    url = 'https://api.tropo.com/1.0/sessions?%s' % urlencode({action:'create', token:token, numbertodial:customer_id, msg:message})
    call = requests.get(url,headers={'content-type':'application/x-www-form-urlencoded'})
    return call


def smartsheet_log_signup(customer_id, signup_time):
    """
    Create row in smartsheet based on environment variables
    """
    signup_sheet_name = current_app.config['SMARTSHEET_SIGNUP_SHEET']
    smartsheet_token = current_app.config['SMARTSHEET_TOKEN']

    smartsheet = smartsheet.Smartsheet(smartsheet_token)
    action = smartsheet.Sheets.list_sheets(include_all=True)
    sheets = action.data
    for sheetInfo in sheets:
        if sheetInfo.name == signup_sheet_name:
            sheet = smartsheet.Sheets.get_sheet(sheetInfo.id)
            break

    else:
        print("Failed logging signup from %s. A smartsheet named %s wasn't found under token %s" % (customer_id, signup_sheet_name, smartsheet_token))

    columns = smartsheet.Sheets.get_columns(sheetInfo.id)
    row = smartsheet.models.Row()
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

    return smartsheet.Sheets.add_rows(sheetInfo.id, [row])

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

    # create a new team room for the customer
    room = api.rooms.create(customer_id, teamId=team_id)

    # create webhook for new room
    # FIXME
    target_url = url_for('.')
    resource = ""
    event = ""
    filter_ = ""
    secret = target_url + '12345'
    webhook = api.webhook.create(room.title + ' create', target_url, resource, event, filter_, secret)

    #smartsheet_log_signup(customer_id, datetime.now())

    return room

