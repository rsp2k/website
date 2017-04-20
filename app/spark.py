import ciscosparkapi

from app import config
from app import tropo


def create_room_webhook(room, webhook_url):
    """
    Create the webhook if it doesn't already exist. The Webhook is triggered when new messages are posted to the room.
    :param room: Cisco Spark Room object to create webhook in 
    :param webhook_url: URL for webhook to POST JSON payload to
    :return: Cisco Spark Webhook object.
    """
    # Create when
    #  a message
    resource = "messages"
    # is created
    event = "created"
    # in the newly created room
    filter_ = "roomId=%s" % room.id

    # insecure example secret used to generate the payload signature
    secret = webhook_url + '12345'

    # Connect to SparkAPI with SPARK_TOKEN
    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=config.SPARK_TOKEN)

    # search webhooks items for matching
    for webhook in spark_api.webhooks.list():
        if webhook.resource == resource and webhook.event == event and webhook.filter == filter_:
            break
    else:
        webhook = spark_api.webhooks.create(room.title + 'messages created',
            webhook_url, resource, event, filter_, secret)

    return webhook

def customer_room_message_send(customer_id, **room_args):
    """
    Posts message to customer's Spark Room for customer_id using room_args. Room/Webhook will be created if necessary.
    :param customer_id: Customer Phone Number (may start with 1)
    :param room_args: text/markup/file/webhook_url
    :return: Cisco Spark Message object 
    """

    # Basic sanity checking
    if 'text' not in room_args and 'markup' not in room_args and 'files' not in room_args:
        raise PassedParametersError("Must specify at least one of text/markup/files")

    # setup Spark API connection using SPARK_TOKEN
    spark_api = ciscosparkapi.CiscoSparkAPI(access_token=config.SPARK_TOKEN)

    # NOTE: Spaces are still called rooms in the API, confusing, I know :)

    # loop through rooms for SPARK_AGENT_TEAM_ID, looking for customer room
    for room in spark_api.rooms.list(teamId=config.SPARK_AGENT_TEAM_ID):
        # Compare first 10 characters of each
        if is_customers_room(room, customer_id):
            break # stop looping if we found the customers room

    # If room is not found and break is never encountered, else block runs
    # http://book.pythontips.com/en/latest/for_-_else.html
    else:
        # New customer
        room = customer_new_signup(spark_api, customer_id, config.SPARK_AGENT_TEAM_ID, room_args['text'], room_args['webhook_url'])

    # remove webhook url since spark API doesn't accept it
    del(room_args['webhook_url'])
    # post the message to spark room
    return spark_api.messages.create(roomId=room.id, **room_args)

class PassedParametersError(Exception):
    pass

def is_customers_room(room, customer_id):
    """
    Check if given room belongs to customer_id. Looks at last 10 characters of each
    :param room: Spark Room Object
    :param customer_id: Customer Phone Number (may start with 1)
    :return: True or False
    """
    if room.title[-10:] is customer_id[:-10]:
        return True
    return False

def customer_new_signup(spark_api, customer_id, team_id, message_from_customer, webhook_url):
    """
    Create room/webhook and post message room then send customer SMS
    :param spark_api: Cisco Spark API Object
    :param customer_id: Customer Phone Number (may start with 1)
    :param team_id: Team ID to create Customer Room under
    :param message_from_customer: Text of message sent from customer when they signed up
    :param webhook_url: URL to use when creating webhook
    :return: Cisco Spark Room objecct
    """

    # Send message via tropo
    message = "Thanks for signing up! To get in touch, reply to this message or call this number during business hours."
    tropo.send_sms(customer_id, message)

    for room in spark_api.rooms.list():
        if is_customers_room(room, customer_id):
            break
    else:
        # create a new team room for the customer
        # http://ciscosparkapi.readthedocs.io/en/latest/user/api.html#ciscosparkapi.RoomsAPI.create
        room = spark_api.rooms.create(customer_id, teamId=team_id)

    # create webhook for new room
    # http://ciscosparkapi.readthedocs.io/en/latest/user/api.html#ciscosparkapi.WebhooksAPI.create
    webhook = create_room_webhook(room, webhook_url)

    # OPTIONALLY CALL SMARTSHEET IF VARS ARE FILLED OUT IN app/config.py
    # from app.smartsheet_log import smartsheet_log_signup
    # smartsheet_log_signup(customer_id, datetime.now(), message_from_customer)

    return room
