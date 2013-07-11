import datetime
from flask.ext.wtf import Form, TextField, BooleanField
from flask.ext.wtf import Required, validators, ValidationError

from poisk.models import ActionToken

class LoginForm(Form):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=True)

class PinLoginForm(Form):
    pin = TextField('pin', validators=[Required()])
    remember_me = BooleanField('remember_me', default=True)

    def validate_pin(form, field):
        print 'fooooo'
        token = ActionToken.query.filter(ActionToken.hash==field.data).first()
        if not token:
            raise ValidationError('Invalid PIN')
        if (token.created - datetime.datetime.utcnow()) > datetime.timedelta(minutes=5):
            raise ValidationError('PIN expired')

class ProfileForm(Form):
    name = TextField('Name', validators=[Required()])
    email = TextField('Email Address', [validators.Length(min=6)])
    is_public = BooleanField('Public', default=False)

class KeyNewForm(Form):
    name = TextField('Name', validators=[Required()])
