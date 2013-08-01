from flask import (
    render_template, g, request, flash,
)

from flask.ext.login import current_user

from poisk import app, lm, babel
from poisk.models import db, User, AnonUser, Key, KeyTransaction, change_key_holder
from poisk.helpers import redirect_back, keyholder_required

openid_url = 'https://id.kreativitaet-trifft-technik.de/openidserver/users/'


@babel.timezoneselector
def get_timezone():
    return 'Europe/Berlin'

@babel.localeselector
def get_locale():
    return 'de_DE'

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

lm.anonymous_user = AnonUser

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
def index():
    keys = Key.query.outerjoin(Key.current_transaction).order_by(db.desc(KeyTransaction.start)).all()
    keyholders = []
    if g.user.is_keyholder:
        keyholders = User.query.filter(User.is_keyholder==True).all()
    return render_template("index.html", keys=keys, keyholders=keyholders)

@app.route('/keys')
@keyholder_required
def keys():
    keys = Key.query.all()
    keyholders = User.query.filter(User.is_keyholder==True).all()
    return render_template("keys.html", keys=keys, keyholders=keyholders)

@app.route('/key/<int:key_id>')
@keyholder_required
def key(key_id):
    query = KeyTransaction.query.filter(KeyTransaction.key_id==key_id)
    transactions = query.order_by(db.desc(KeyTransaction.start)).limit(50).all()
    key = Key.query.get(key_id)
    return render_template("key.html", key=key, transactions=transactions)

@app.route('/key/<int:key_id>/take', methods=['POST'])
@keyholder_required
def key_take(key_id):
    key = Key.query.get(key_id)
    change_key_holder(key, g.user)
    db.session.commit()
    return redirect_back('keys')

@app.route('/key/<int:key_id>/change_keyholder', methods=['POST'])
@keyholder_required
def change_keyholder(key_id):
    user = User.query.get(request.form['keyholder_id'])
    key = Key.query.get(key_id)
    change_key_holder(key, user)
    db.session.commit()
    flash("changed keyholder for %s to %s" % (key.name, user), 'success')
    return redirect_back('admin_keys')

@app.route('/about')
def about():
    return render_template('about.html')

