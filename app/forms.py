from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.widgets import Input
from wtforms.validators import Required, Email
from wtforms import ValidationError

import phonenumbers

class SignupForm(FlaskForm):
    name = TextField(u'Your name', validators=[Required()])
    password = TextField(u'Your favorite password', validators=[Required()])
    email = TextField(u'Your email address', validators=[Email()])
    phone = StringField('Phone', validators=[Required()])

    birthday = DateField(u'Your birthday')

    a_float = FloatField(u'A floating point number')
    a_decimal = DecimalField(u'Another floating point number')
    a_integer = IntegerField(u'An integer')

    now = DateTimeField(u'Current time',
                        description='...for no particular reason')
    sample_file = FileField(u'Your favorite file')
    eula = BooleanField(u'I did not read the terms and conditions',
                        validators=[Required('You must agree to not agree!')])

    submit = SubmitField(u'Signup')


    def validate_phone(form, field):
        if len(field.data) > 16:
            raise ValidationError('Invalid phone number.')
        try:
            input_number = phonenumbers.parse(field.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')
        except:
            input_number = phonenumbers.parse("+1"+field.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')
