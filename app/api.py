# This contains our api; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

from flask import Blueprint, render_template, redirect, url_for

api = Blueprint('api', __name__)

# Our api index-page just shows a quick explanation from "templates/api.html"
@api.route('/')
def index():
    return render_template('api.html')

