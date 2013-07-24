# manage.py

from flask.ext.script import Manager, Server

from poisk import app
from poisk.models import db, User, Key

manager = Manager(app)
manager.add_command("runserver", Server(threaded=True, use_reloader=True))

@manager.command
def init_db():
    db.create_all()

    for k in 'Zuse Lovelace Colmar Turing Pascal Yazu Babbage Napier'.split():
        db.session.add(Key(name=k))

    u = User('olt')
    u.is_keyholder = True
    u.is_admin = True
    db.session.add(u)
    u = User(None)
    u.is_keymanager = True
    u.name = "Surfstation"
    db.session.add(u)
    db.session.commit()


if __name__ == "__main__":
    manager.run()
