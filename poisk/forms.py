from flask.ext.wtf import Form, TextField, BooleanField
from flask.ext.wtf import Required, validators

class LoginForm(Form):
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=True)

class ProfileForm(Form):
    name = TextField('Name', validators=[Required()])
    email = TextField('Email Address', [validators.Length(min=6)])
