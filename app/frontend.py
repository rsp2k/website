# This contains our frontend; since it is a bit messy to use the @app.route
# decorator style when using application factories, all of our routes are
# inside blueprints. This is the front-facing blueprint.
#
# You can find out more about blueprints at
# http://flask.pocoo.org/docs/blueprints/

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from markupsafe import escape

from .forms import ContactForm
from .nav import nav

frontend = Blueprint('frontend', __name__)

# Menu / navbar
nav.register_element('frontend_top', Navbar(
    View('Acme Corp', 'frontend.index'),
    View('Home', 'frontend.index'),
    View('Contact', 'frontend.contact'),
    Link('GitHub','https://github.com'),
    Subgroup(
        'Spark',
        Link('My Apps', 'https://developer.ciscospark.com/apps.html'),
        Link('Quick Reference', 'https://developer.ciscospark.com/quick-reference.html'),
        Link('ciscosparkapi', 'https://github.com/CiscoDevNet/ciscosparkapi'),
        Link('WebHooks', 'https://developer.ciscospark.com/webhooks-explained.html'),
        Link('Bots', 'https://developer.ciscospark.com/bots.html'),
        Link('Admin API', 'https://developer.ciscospark.com/admin-api.html'),
        Link('JS SDK Download', 'https://www.npmjs.com/package/ciscospark'),
        Link('JS SDK Docs', 'https://ciscospark.github.io/spark-js-sdk/api/'),
        Link('Innovation Fund', 'https://developer.ciscospark.com/fund/'),
    ),
    Subgroup(
       'Tropo',
       Link('Python Module', 'https://github.com/rsp2k/ciscotropowebapi'),
       Link('WebAPI', 'https://www.tropo.com/docs/webapi'),
       Link('Forums', 'https://support.tropo.com/hc/en-us/community/topics'),
       Link('IRC Chat', 'https://www.tropo.com/help/irc-chat/'),
       Link('Coding Tips', 'https://www.tropo.com/docs/coding-tips'),
       Link('Developer Network', 'https://www.tropo.com/tropo-developer-network/'),
       Link('SparkLog4Tropo', 'https://gist.github.com/ObjectIsAdvantag/b73db0cffcedb1152a2d6669cb3d27b0'),
    ),
   Subgroup(
       'Python',
       Link('Beginners Guide', 'https://wiki.python.org/moin/BeginnersGuide/'),
       Link('Awesome Python', 'https://github.com/vinta/awesome-python'),
       Link('WSGI', 'https://www.python.org/dev/peps/pep-3333/'),
       Link('v3.6 Docs', 'https://docs.python.org/3/'),
    ),
    Subgroup(
       'Web Developer Docs',
       Link('Flask-Bootstrap', 'http://pythonhosted.org/Flask-Bootstrap'),
       Link('Flask-AppConfig', 'https://github.com/mbr/flask-appconfig'),
       Link('Flask-Debug', 'https://github.com/mbr/flask-debug'),
       Separator(),
       Text('Bootstrap'),
       Link('Getting started', 'http://getbootstrap.com/getting-started/'),
       Link('CSS', 'http://getbootstrap.com/css/'),
       Link('Components', 'http://getbootstrap.com/components/'),
       Link('Javascript', 'http://getbootstrap.com/javascript/'),
       Link('Customize', 'http://getbootstrap.com/customize/'), ),
    Text('Using Flask-Bootstrap {}'.format(FLASK_BOOTSTRAP_VERSION)), ))

# Simple Homepage
@frontend.route('/')
def index():
    return render_template('index.html')

# Simple contact form
@frontend.route('/contact/', methods=('GET', 'POST'))
def contact():
    form = ContactForm()

    if request.method == 'POST' and form.validate():
        # We don't have anything fancy in our application, so we are just
        # flashing a message when a user completes the form successfully.
        #
        # Note that the default flashed messages rendering allows HTML, so
        # we need to escape things if we input user values:
        flash('Hello, {}. You have successfully signed up'
              .format(escape(form.name.data)))

        # In a real application, you may wish to avoid this tedious redirect.
        return redirect(url_for('.index'))

    return render_template('contact.html', form=form)
