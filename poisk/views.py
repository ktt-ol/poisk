import flask
from flask import (
    render_template, g, session, request, redirect, flash, url_for,
    abort,
)

from flask.ext.login import current_user, login_user

from poisk import app, lm, oid
from poisk.models import db, User
from poisk.forms import LoginForm, ProfileForm

openid_url = 'https://id.kreativitaet-trifft-technik.de/openidserver/users/'


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
def index():
    return render_template("index.html")


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
    session['openid'] = openid_name
    user = User.query.filter_by(nick=openid_name).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        login_user(user)
        return redirect(oid.get_next_url())
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
        flash(u'Profile successfully created')
        user = User(session['openid'])
        user.email = form.email.data
        user.name = form.name.data
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(oid.get_next_url())

    if request.method == 'GET':
        form.name.data = request.args.get('name')
        form.email.data = request.args.get('email')

    return render_template('create_profile.html', next_url=oid.get_next_url(),
        errors=form.errors, form=form)


@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates a profile"""
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db.session.delete(g.user)
            db.session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('index'))
        form['name'] = request.form['name']
        form['email'] = request.form['email']
        if not form['name']:
            flash(u'Error: you have to provide a name')
        elif '@' not in form['email']:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.user.name = form['name']
            g.user.email = form['email']
            db.session.commit()
            return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)


@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())


