import os
basedir = os.path.abspath(os.path.dirname(__file__))

# use DEBUG only for local testing
# DEBUG = True

CSRF_ENABLED = True

# use new secret key for each installatino, never commit/publish it
SECRET_KEY = 'fLuidIU(*ND£LKjnD(DNLKJS'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

LOG_FILE = os.path.join(basedir, 'poisk.log')
ADMIN_EMAILS = []
