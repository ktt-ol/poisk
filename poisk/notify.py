import textwrap
from flask import url_for, current_app
from flask.ext.mail import Message
from poisk import mail
from poisk.models import User

def notify_admins_new_user(user):
    admins = User.query.filter_by(is_admin=True).all()
    msg = Message(
        "New Poisk user registered: %s" % user.nick,
        sender=current_app.config['ADMIN_EMAILS'][0],
        recipients=[a.email for a in admins],
    )
    msg.body = textwrap.dedent("""
                           %s registered at Poisk.
                           See: %s
                           """ % (user, url_for('admin.users', _external=True))
                           )
    try:
        mail.send(msg)
    except Exception:
        current_app.logger.exception("error sending mail")


def notify_key_given(user, key, giver):
    if not user.email:
        return

    msg = Message(
        "Poisk: %s gave you %s" % (giver.nick, key.name),
        sender=current_app.config['ADMIN_EMAILS'][0],
        recipients=[user.email],
    )
    msg.body = textwrap.dedent("""
                           Congratulations, you are now the keyholder of %s.
                           Please blame %s.
                           """ % (key.name, giver)
                           )

    try:
        mail.send(msg)
    except Exception:
        current_app.logger.exception("error sending mail")

