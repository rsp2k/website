# This contains our api; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

# Python standard library modules
import hashlib
import hmac
import logging
import os
from datetime import datetime

import ciscosparkapi
import ciscotropowebapi
from flask import Blueprint, render_template, url_for, request, current_app, abort

from app import config

from app import tropo
from app import spark

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
    return tropo.webhook_process(request)

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
    webhook_key = config.SPARK_WEBHOOK_KEY

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

    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=config.SPARK_TOKEN)
    # Get the room info from room id that was passed from webhook
    room = spark_api.rooms.get(message.room.id)

    # customer id is room name
    customer_id = room.title

    tropo.send_sms(customer_id, message.text)

    return 'OK'

@api.route('/customer_room_message_post/', methods=['GET'])
def customer_room_post_message_get():
    return render_template('customer-room-post-message.html')


@api.route('/customer_room_message_post/', methods=['POST'])
def customer_room_post_message_post():
    """
    API endpoint to customer_room_post_message

Expects JSON data with customer_id and message
    """

    # make sure we have the data necessary to process the request
    if not request.json:
        abort(400)

    if not ('customer_id' in request.json and ('text' in request.json or 'markdown' in request.json)):
        abort(400)

    # let flask build an external url based on SERVER_NAME
    webhook_url = url_for('.spark_webhook_post', _external=True)

    # initialize dictionary with customer id
    args = {'customer_id': request.json['customer_id'], 'webhook_url':webhook_url}

    # loop over allowed API parameters to be passed to function and add if found in JSON
    allowed_parameters = ['text', 'markdown', 'files']
    for parameter in allowed_parameters:
        if parameter in request.json:
            args[parameter] = request.json[parameter]


    # pass customer id and upacked args to function
    message = spark.customer_room_message_send(request.json['customer_id'],**args)

    if not message:
       abort(500)

    return 'OK'


