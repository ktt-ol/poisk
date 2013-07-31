import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.babel import Babel
from config import basedir

app = Flask(__name__)
app.config.from_object('config')
babel = Babel(app)
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from poisk.views import admin, api, main

app.register_blueprint(admin.admin, url_prefix='/admin')
app.register_blueprint(api.api, url_prefix='/api')


import logging
from logging.handlers import SMTPHandler

if not app.debug and app.config.get('ADMIN_EMAILS'):
    mail_handler = SMTPHandler('127.0.0.1',
                               'poisk-error@kreativitaet-trifft-technik.de',
                               app.config['ADMIN_EMAILS'], 'Poisk Failed')
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
'''))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

if not app.debug and app.config.get('LOG_FILE'):
    file_handler = logging.FileHandler(app.config['LOG_FILE'])
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
