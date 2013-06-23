# manage.py

from flask.ext.script import Manager

from poisk import app
from poisk.models import db, User, Key

manager = Manager(app)

@manager.command
def init_db():
    db.create_all()
    db.session.commit()


if __name__ == "__main__":
    manager.run()
