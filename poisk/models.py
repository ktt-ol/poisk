from flask import g
from datetime import datetime
from flask.ext.login import AnonymousUserMixin
from poisk import db

from sqlalchemy.sql import functions

class KeyTransaction(db.Model):
    __tablename__ = 'key_transactions'

    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey('keys.id'))
    key = db.relationship('Key', foreign_keys=[key_id])
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    holder = db.relationship('User', foreign_keys=[holder_id], lazy='joined')
    start = db.Column(db.DateTime, default=datetime.utcnow)
    end = db.Column(db.DateTime)

def change_key_holder(key, holder):
    if key.current_transaction:
        key.current_transaction.end = datetime.utcnow()
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
    nick = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    last_seen = db.Column(db.DateTime)
    is_keyholder = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean)
    is_keymanager = db.Column(db.Boolean)

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
            if not self.nick:
                return self.name
            return "%s (%s)" % (self.nick, self.name)
        return self.nick

    @property
    def public_name(self):
        if self.is_public:
            return unicode(self)
        if not self.nick: # special users are "public"
            return self.name
        return self.nick

class AnonUser(AnonymousUserMixin):
    is_admin = False
    is_keyholder = False
    is_keymanager = False

class Key(db.Model):
    __tablename__ = 'keys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    holder = db.relationship('User', backref='keys', lazy='joined')
    current_transaction_id = db.Column(db.Integer, db.ForeignKey('key_transactions.id', use_alter=True, name='fk_key_key_transactions_id'))
    current_transaction = db.relationship('KeyTransaction', foreign_keys=[current_transaction_id], post_update=True)
    allocated = db.Column('allocated', db.Boolean, default=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Key %r>' % self.name

    @property
    def last_activity(self):
        date = max(self.holder.last_seen or datetime.fromtimestamp(0),
                   self.current_transaction.start or datetime.fromtimestamp(0))
        return datetime.utcnow() - date

    @property
    def last_activity_str(self):
        if self.allocated:
            return ''
        dt = self.last_activity
        hours = dt.seconds / 60 / 60 % 24
        if not dt.days and not hours:
            return ''
        return "%dd%dh" % (dt.days, hours)

    @classmethod
    def query_ordered(cls):
        # order by most recent last_seen OR key transaction
        newest_date = functions.max(
            functions.coalesce(User.last_seen, 0),
            functions.coalesce(KeyTransaction.start, 0)
        )
        query = Key.query.outerjoin(Key.holder).outerjoin(Key.current_transaction)
        return query.order_by(db.desc(newest_date))

class ActionToken(db.Model):
    __tablename__ = 'action_tokens'
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String, unique=True, nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')

