import os
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

CSRF_ENABLED = True
SECRET_KEY = 'lakfdj02r03ijd023ijdo3knsdkjfn'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
