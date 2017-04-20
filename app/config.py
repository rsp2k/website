# User defined variables
# to use these in you app you must first 'from app import config', prefix variable names in this file with config.
# Eg, SERVERNAME in this file would be availabe as config.SERVER_NAME after the import

# dCloud external URL, used when creating Spark webhook
SERVER_NAME = 'webapp.vpod651.dc-01.com'

# Phone number to redirect inbound voice calls to
CUSTOMER_SERVICE_REDIRECT_DN = ''

# Key for Tropo Send SMS application
TROPO_KEY = '554c4d714b7559414e4a566948424c424c6875686175644e67574e475156586e67646a7941414450734f7347'

# Spark token
SPARK_TOKEN = 'MTY3MGQ3N2EtYzhmYS00OTM0LTgyZWItNGM0Njk2NGUxNjZiOGJlZmExMzctZmY3'

# Id of Agent Team to create customer rooms under
SPARK_AGENT_TEAM_ID = '31e512f0-255a-11e7-8d30-31c79ab2bd59'

# Optional: Used to validate webhook request came from Spark
SPARK_WEBHOOK_KEY = ''

# Optional Smart Sheet integration
SMARTSHEET_TOKEN = ''

# Sheet Name
SMARTSHEET_SIGNUP_SHEET = ''

# Column Names
SMARTSHEET_COL_SIGNUP_TIME = ''
SMARTSHEET_COL_CUSTOMER_ID = ''
SMARTSHEET_COL_MESSAGE = ''