# manage.py

from flask.ext.script import Manager, Shell

from poisk import app, models
from poisk.status import SpaceStatus
from poisk.notify import notify_stale_keyholder
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


@manager.command
def poke(doit=False):
    keyholders = User.query_keyholders().all()
    for k in keyholders:
        for key in k.keys:
            if key.allocated:
                continue
            if key.last_activity.days in (3, 5, 7) or key.last_activity.days >= 10:
                notify_stale_keyholder(k, key, doit=doit)

@manager.command
def runserver(port=5000):
    status = SpaceStatus()
    status.start()

    app.run(port=int(port), threaded=True, use_reloader=True)


if __name__ == "__main__":
    import os
    if os.environ.get('DEBUG') == '1':
        app.debug = True
    manager.run()
