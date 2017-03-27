# This contains our api; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

from flask import Blueprint, render_template, redirect, url_for, request

from datetime import datetime

from ciscosparkapi import CiscoSparkAPI
from tropo import Tropo, Session
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
    Recieve POST from Tropo on inbound voice/sms call
    """

# FIXME PARSE Customer ID and message

    customer_room_post_message(customer_id, { message: request.json['message'] }):
    return 'OK'

@api.route('/spark-webhook', methods=['GET'])
def spark_webhook_get():
    return 'Try POST?'

@api.route('/spark-webhook', methods=['POST'])
def spark_webhook_post():
    """
    Receive data from Spark webhooks
    """

# FIXME PARSE Customer ID, mention and message

# FIXME check for mention before sending

    send_customer_sms(customer_id, message):

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

    args = {
        customer_id: request.json['customer_id'],
        message: request.json['message'],
        markdown: request.json['markdown'],
        files: request.json['files'],
    }

    message = customer_room_post_message(customer_id, args):

    if not message:
       abort(500)

    return 'OK'

def customer_room_post_message(customer_id, **kwargs):
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
    return api.messages.create(roomId=room.id, **kwargs)

def send_customer_sms(customer_id, message):
    """
    Generic function to send customer_id message via SMS
    """

    t = Tropo()
    t.call(to="+%s" % customer_id, network = "SMS")
    t.say(message)

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
        print "Failed logging signup from %s. A smartsheet named %s wasn't found under token %s" % (customer_id, signup_sheet_name, smartsheet_token)

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
    or some other asyc job queue to keep users from waiting/isolate from errors
    """

    # Send message via tropo
    message = "Thanks for signing up! To get in touch, reply to this message or call this number during business hours."
    send_customer_sms(customer_id, message)

    # create a new team room for the customer
    room = api.rooms.create(customer_id, teamId=team_id)

    smartsheet_log_signup(customer_id, datetime.now()):

    return room

