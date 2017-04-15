"""
Entry point for app
"""

import os

from flask import Flask

from flask_appconfig import AppConfig
from flask_appconfig.env import from_envvars
from flask_bootstrap import Bootstrap

from .frontend import frontend
from .api import api
from .nav import nav


def create_app(configfile=None):
    """
    Application Factory - see http://flask.pocoo.org/docs/patterns/appfactories/
    """
    app = Flask(__name__)

    # https://pythonhosted.org/Flask-Bootstrap/
    Bootstrap(app)

    # Load blueprints
    # http://flask.pocoo.org/docs/0.12/blueprints/

    # Website
    app.register_blueprint(frontend)

    # API endpoints
    app.register_blueprint(api, url_prefix='/api')

    # http://pythonhosted.org/flask-nav/
    nav.init_app(app)

    return app
