from urlparse import urlparse, urljoin
import random
from functools import wraps
from flask import (
    render_template, g, session, request, redirect, flash, url_for,
    abort, jsonify,
)

from flask.ext.login import current_user, login_user, login_required, logout_user

from poisk import app, lm, oid, babel
from poisk.models import db, User, AnonUser, Key, KeyTransaction, change_key_holder, ActionToken
from poisk.forms import LoginForm, ProfileForm, KeyNewForm, PinLoginForm

openid_url = 'https://id.kreativitaet-trifft-technik.de/openidserver/users/'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_authenticated():
            return redirect(url_for('login', next=request.url))
        if not g.user.is_admin:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def keyholder_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_authenticated():
            return redirect(url_for('login', next=request.url))
        if not g.user.is_keyholder and not g.user.is_keymanager:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

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

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(oid.get_next_url())
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        openid = openid_url + form.openid.data
        return oid.try_login(openid, ask_for=['email', 'fullname',
                                                  'nickname'])

    return render_template('login.html', next=oid.get_next_url(),
        form=form, error=oid.fetch_error())

@app.route('/login/pin', methods=['GET', 'POST'])
def login_pin():
    form = PinLoginForm()
    if form.validate_on_submit():
        token = ActionToken.query.filter(ActionToken.hash==form.pin.data).first()
        login_user(token.user)
        db.session.delete(token)
        db.session.commit()
        flash('logged in')
        return redirect_back('index')
    return render_template('login_pin.html', next=oid.get_next_url(),
        form=form)

@oid.after_login
def create_or_login(resp):
    """This is called when login with OpenID succeeded and it's not
    necessary to figure out if this is the users's first login or not.
    This function has to redirect otherwise the user will be presented
    with a terrible URL which we certainly don't want.
    """
    openid_name = resp.identity_url.rsplit('/', 2)[-1]
    user = User.query.filter_by(nick=openid_name).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        login_user(user)
        return redirect(oid.get_next_url())
    session['openid'] = openid_name
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """If this is the user's first login, the create_or_login function
    will redirect here so that the user can set up his profile.
    """
    if g.user.is_authenticated() or 'openid' not in session:
        return redirect(url_for('index'))

    form = ProfileForm()
    if form.validate_on_submit():
        flash(u'Profile successfully created', 'success')
        user = User(session['openid'])
        user.email = form.email.data
        user.name = form.name.data
        db.session.add(user)
        db.session.commit()
        login_user(user)
        session.pop('openid')
        return redirect(oid.get_next_url())

    if request.method == 'GET':
        form.name.data = request.args.get('name')
        form.email.data = request.args.get('email')

    return render_template('create_profile.html', next_url=oid.get_next_url(),
        errors=form.errors, form=form)


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_show(user_id):
    if user_id != g.user.id:
        user = User.query.get(user_id)
        return render_template('user.html', user=user)
    form = ProfileForm(obj=g.user)
    if form.validate_on_submit():
        if 'delete' in request.form:
            db.session.delete(g.user)
            db.session.commit()
            logout_user()
            flash(u'Profile deleted', 'success')
            return redirect(url_for('index'))
        flash(u'Profile successfully created', 'success')
        g.user.name = form.name.data
        g.user.email = form.email.data
        g.user.is_public = form.is_public.data
        db.session.commit()
        return redirect(url_for('user_show', user_id=user_id))
    return render_template('edit_profile.html', form=form)

@app.route('/user/<int:user_id>/createpin')
def pin_create(user_id):
    if g.user.id != user_id and not g.user.is_admin:
        return abort(403)

    ActionToken.query.filter(ActionToken.user==g.user).delete()
    token = ActionToken()
    token.user_id = user_id
    token.hash = "%06d" % random.randint(0, 999999)
    db.session.add(token)
    db.session.commit()
    return render_template('token_show.html', token=token)

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/keys', methods=['GET', 'POST'])
@admin_required
def admin_keys():
    keys = Key.query.all()
    keyholders = User.query.filter(User.is_keyholder==True).all()
    return render_template('admin_keys.html', keys=keys, keyholders=keyholders)

@app.route('/user/<user_id>/change_keyholder', methods=['POST'])
@admin_required
def change_is_keyholder(user_id):
    is_keyholder = request.form['keyholder'].lower() == 'true'
    user = User.query.get(user_id)
    user.is_keyholder = is_keyholder
    db.session.commit()
    flash("changed keyholder status for %s" % user.nick, 'success')
    return redirect_back("admin_users")

@app.route('/user/<int:user_id>/change_admin', methods=['POST'])
@admin_required
def change_is_admin(user_id):
    is_admin = request.form['admin'].lower() == 'true'
    if g.user.id == user_id:
        raise abort(400, "can't change own admin status")
    user = User.query.get(user_id)
    user.is_admin = is_admin
    db.session.commit()
    flash("changed admin status for %s" % user.nick, 'success')
    return redirect_back("admin_users")

@app.route('/key/<int:key_id>/change_keyholder', methods=['POST'])
@keyholder_required
def change_keyholder(key_id):
    user = User.query.get(request.form['keyholder_id'])
    key = Key.query.get(key_id)
    change_key_holder(key, user)
    db.session.commit()
    flash("changed keyholder for %s to %s" % (key.name, user.nick), 'success')
    return redirect_back('admin_keys')

@app.route('/key/add', methods=['GET', 'POST'])
@admin_required
def admin_key_add():
    form = KeyNewForm()
    if form.validate_on_submit():
        key = Key(form.name.data)
        db.session.add(key)
        db.session.commit()
        flash('Key added', 'success')
        return redirect_back('admin_keys')
    return render_template('key_add.html', form=form)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    logout_user()
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())

@app.route('/api/v1/keyholder.json')
def api_keyholder():
    current_keyholder = User.query.join(User.keys).all()
    last_transaction = KeyTransaction.query.order_by(db.desc(KeyTransaction.start)).first()
    resp = jsonify(
        current_keyholder=[k.nick for k in current_keyholder if k.nick],
    )
    resp.date = last_transaction.start
    resp.add_etag()
    resp.make_conditional(request)
    return resp

def redirect_back(endpoint, **values):
    target = get_redirect_target()
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc
