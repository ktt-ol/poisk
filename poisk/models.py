from flask import g
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import AnonymousUserMixin

db = SQLAlchemy()


class KeyTransaction(db.Model):
    __tablename__ = 'key_transactions'

    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey('keys.id'))
    key = db.relationship('Key', foreign_keys=[key_id])
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    holder = db.relationship('User', foreign_keys=[holder_id], lazy='joined')
    start = db.Column(db.DateTime, default=datetime.now)
    end = db.Column(db.DateTime)

def change_key_holder(key, holder):
    if key.current_transaction:
        key.current_transaction.end = datetime.now()
    tx = KeyTransaction()
    tx.user = g.user
    tx.key = key
    tx.holder = holder
    key.current_transaction = tx
    key.holder = holder
    db.session.add(tx)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    is_keyholder = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __init__(self, nick):
        self.nick = nick

    def __repr__(self):
        return '<User %r>' % self.nick

    def __str__(self):
        if self.name:
            return "%s (%s)" % (self.nick, self.name)
        return self.nick

class AnonUser(AnonymousUserMixin):
    is_admin = False
    is_keyholder = False

class Key(db.Model):
    __tablename__ = 'keys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    holder = db.relationship('User', backref='keys', lazy='joined')
    current_transaction_id = db.Column(db.Integer, db.ForeignKey('key_transactions.id', use_alter=True, name='fk_key_key_transactions_id'))
    current_transaction = db.relationship('KeyTransaction', foreign_keys=[current_transaction_id], post_update=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Key %r>' % self.name


