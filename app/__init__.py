"""
Entry point for app
"""

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

    # http://pythonhosted.org/flask-appconfig/
    AppConfig(app)

    # FIXME
    # Load config from environment variables that start with a prefix of MYAPP_
    #from_envvars(app.config, prefix=app.name.upper() + '_')

    # https://pythonhosted.org/Flask-Bootstrap/
    Bootstrap(app)

    # https://pythonhosted.org/Flask-Bootstrap/
    app.register_blueprint(frontend)
    app.register_blueprint(api, url_prefix='/api')

    # use our own bootstrap
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    # http://pythonhosted.org/flask-nav/
    nav.init_app(app)

    return app
