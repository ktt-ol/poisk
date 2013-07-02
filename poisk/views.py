from functools import wraps
from flask import (
    render_template, g, session, request, redirect, flash, url_for,
    abort,
)

from flask.ext.login import current_user, login_user, login_required, logout_user

from poisk import app, lm, oid
from poisk.models import db, User, Key
from poisk.forms import LoginForm, ProfileForm, KeyNewForm

openid_url = 'https://id.kreativitaet-trifft-technik.de/openidserver/users/'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_authenticated() or not g.user.is_admin:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def keyholder_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_authenticated() or not g.user.is_keyholder:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
def index():
    keys = Key.query.all()
    return render_template("index.html", keys=keys)

@app.route('/keys')
@keyholder_required
def keys():
    keys = Key.query.all()
    keyholders = User.query.filter(User.is_keyholder==True).all()
    return render_template("keys.html", keys=keys, keyholders=keyholders)

@app.route('/key/<int:key_id>/take', methods=['POST'])
@oid.loginhandler
def key_take(key_id):
    key = Key.query.get(key_id)
    key.holder = g.user
    db.session.commit()
    return redirect(url_for('keys'))

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


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
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
        return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin():
    users = User.query.all()
    keys = Key.query.all()
    keyholders = User.query.filter(User.is_keyholder==True).all()
    return render_template('admin_list.html', users=users, keys=keys, keyholders=keyholders)

@app.route('/user/<user_id>/change_keyholder', methods=['POST'])
@admin_required
def change_is_keyholder(user_id):
    is_keyholder = request.form['keyholder'].lower() == 'true'
    user = User.query.get(user_id)
    user.is_keyholder = is_keyholder
    db.session.commit()
    flash("changed keyholder status for %s" % user.nick, 'success')
    return redirect(url_for("admin"))

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
    return redirect(url_for("admin"))

@app.route('/key/<int:key_id>/change_keyholder', methods=['POST'])
@keyholder_required
def change_keyholder(key_id):
    user = User.query.get(request.form['keyholder_id'])
    key = Key.query.get(key_id)
    key.holder = user
    db.session.commit()
    flash("changed keyholder for %s to %s" % (key.name, user.nick), 'success')
    return redirect(url_for("admin"))

@app.route('/key/new', methods=['GET', 'POST'])
@admin_required
def key_new():
    form = KeyNewForm()
    if form.validate_on_submit():
        key = Key(form.name.data)
        db.session.add(key)
        db.session.commit()
        flash('Key added', 'success')
        return redirect(url_for("admin"))
    return render_template('key_add.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())


