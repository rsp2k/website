from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.validators import Required, Email

class ContactForm(FlaskForm):
    name = TextField(u'Your name', validators=[Required()])
    email = TextField(u'Your email address', validators=[Email()])
    phone = TextField(u'Your phone number')
    message = TextAreaField('Your message:', validators=[Required()])

    submit = SubmitField(u'Signup')


