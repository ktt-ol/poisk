# manage.py

from flask.ext.script import Manager, Server, Shell

from poisk import app, models
from poisk.models import db, User, Key

def _make_context():
    return dict(
        app=app,
        db=db,
        models=models,
        User=User,
        Key=Key,
    )

manager = Manager(app)
manager.add_command("runserver", Server(threaded=True, use_reloader=True))
manager.add_command("shell", Shell(make_context=_make_context))

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
    import os
    if os.environ.get('DEBUG') == '1':
        app.debug = True
    manager.run()
