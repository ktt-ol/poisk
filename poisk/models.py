from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


keys_users = db.Table('keys_users',
    db.Column('key_id', db.Integer, db.ForeignKey('keys.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('start', db.DateTime, default=datetime.now),
    db.Column('end', db.DateTime),
)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    is_keyholder = db.Column(db.Boolean)
    is_admin = db.Column(db.Boolean)

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


class Key(db.Model):
    __tablename__ = 'keys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    holder = db.relationship('User', backref='keys')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Key %r>' % self.name


