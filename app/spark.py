import datetime
import logging

import ciscosparkapi
from app import tropo

from flask import url_for

from app import config

def create_room_webhook(room, webhook_url):
    # Create the webhook that is triggered when new messages are posted to the room when
    # a message
    resource = "messages"
    # is created
    event = "created"
    # in the newly created room
    filter_ = "roomId=%s" % room.id

    # insecure example secret used to generate the payload signature
    secret = webhook_url + '12345'

    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=config.SPARK_TOKEN)

    spark_api.webhooks.create(room.title + 'messages created',
            webhook_url, resource, event, filter_, secret)


def customer_room_message_send(customer_id, **room_args):
    """
    Posts message to customer's Spark Room.
    Pass the customer #, the Spark Room ID will be looked up/created for you.
    """

    # Basic sanity checking
    if 'text' not in room_args and 'markup' not in room_args and 'files' not in room_args:
        raise PassedParametersError("Must specify at least one of text/markup/files")

    # setup Spark API connection using SPARK_TOKEN
    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=config.SPARK_TOKEN)

    # NOTE: Spaces are still called rooms in the API, confusing, I know :)

    # get all rooms for SPARK_AGENT_TEAM_ID
    rooms = spark_api.rooms.list(teamId=config.SPARK_AGENT_TEAM_ID)

    # loop through rooms, looking for customer room
    for room in rooms:
        # Compare first 10 characters of each
        if room.title[-10:] is customer_id[:-10]:
            break # stop looping if we found the customers room

    # If room is not found and break is never encountered, else block runs
    # http://book.pythontips.com/en/latest/for_-_else.html
    else:
        # New customer
        room = customer_new_signup(customer_id, config.SPARK_AGENT_TEAM_ID, room_args['text'], room_args['webhook_url'])

    # remove webhook url since spark API doesn't accept it
    del(room_args['webhook_url'])
    # post the message to spark room
    return spark_api.messages.create(roomId=room.id, **room_args)

class PassedParametersError(Exception):
    pass

def customer_new_signup(customer_id, team_id, message_from_customer, webhook_url):
    """
    Called when a new signup occurs
    * post message to customer via SMS and in spark room for agent to see

    """

    # Send message via tropo
    message = "Thanks for signing up! To get in touch, reply to this message or call this number during business hours."
    tropo.send_sms(customer_id, message)

    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=config.SPARK_TOKEN)
    # create a new team room for the customer
    # http://ciscosparkapi.readthedocs.io/en/latest/user/api.html#ciscosparkapi.RoomsAPI.create
    room = spark_api.rooms.create(customer_id, teamId=team_id)

    # create webhook for new room
    # http://ciscosparkapi.readthedocs.io/en/latest/user/api.html#ciscosparkapi.WebhooksAPI.create
    create_room_webhook(room, webhook_url)

    # OPTIONALLY CALL SMARTSHEET IF VARS ARE FILLED OUT IN app/config.py
    # from app.smartsheet_log import smartsheet_log_signup
    # smartsheet_log_signup(customer_id, datetime.now(), message_from_customer)

    return room
