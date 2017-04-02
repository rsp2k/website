# demo-site 

# First Time setup
* Clone this repository
- Create virtualenv
  * python virtualenv venv --python=python3
- Install requirements
  * pip install -r requirements.txt
- Edit TOKENS.py file
  * TROPO_TOKEN
  * SPARK_TOKEN
  - Optional SmartSheet integraton
    * SMARTSHEET_TOKEN
    * SMARTSHEET_SIGNUP_SHEET

# Launch
* Start flask
flask --app uwsgi

# Notes
If you edit template files, you will need to stop and start flask to see the changes, editing python (.py) files fill cause the server to automatically restart.
