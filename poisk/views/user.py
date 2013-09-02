import random
from flask import (
    render_template, g, session, request, redirect, flash, url_for,
    abort, Blueprint,
)

from flask.ext.login import login_user, login_required, logout_user

from poisk import lm, oid
from poisk.models import db, User, AnonUser, ActionToken
from poisk.forms import LoginForm, ProfileForm, PinLoginForm
from poisk.helpers import redirect_back
from poisk.notify import notify_admins_new_user

openid_url = 'https://id.kreativitaet-trifft-technik.de/openidserver/users/'

user = Blueprint("user", __name__)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

lm.anonymous_user = AnonUser


@user.route('/login', methods=['GET', 'POST'])
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

@user.route('/login/pin', methods=['GET', 'POST'])
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
    return redirect(url_for('.create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@user.route('/create-profile', methods=['GET', 'POST'])
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

        notify_admins_new_user(user)

        return redirect(oid.get_next_url())

    if request.method == 'GET':
        form.name.data = request.args.get('name')
        form.email.data = request.args.get('email')

    return render_template('create_profile.html', next_url=oid.get_next_url(),
        errors=form.errors, form=form)

@user.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def show(user_id):
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
        return redirect(url_for('.show', user_id=user_id))
    return render_template('edit_profile.html', form=form)

@user.route('/user/<int:user_id>/createpin')
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

@user.route('/logout')
def logout():
    logout_user()
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())

