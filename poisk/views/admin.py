from flask import (
    render_template, g, request, flash,
    abort, Blueprint, redirect, url_for,
)

from poisk import app
from poisk.forms import KeyNewForm
from poisk.models import db, User, Key
from poisk.helpers import redirect_back

admin = Blueprint('admin', __name__)

@admin.before_request
def restrict_to_admins():
    if not g.user.is_authenticated():
        return redirect(url_for('user.login', next=request.url))
    if not g.user.is_admin:
        return abort(403)

@admin.route('/admin/users', methods=['GET', 'POST'])
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/admin/keys', methods=['GET', 'POST'])
def keys():
    keys = Key.query.all()
    keyholders = User.query.filter(User.is_keyholder==True).all()
    return render_template('admin/keys.html', keys=keys, keyholders=keyholders)

@admin.route('/key/add', methods=['GET', 'POST'])
def key_add():
    form = KeyNewForm()
    if form.validate_on_submit():
        key = Key(form.name.data)
        db.session.add(key)
        db.session.commit()
        flash('Key added', 'success')
        return redirect_back('admin_keys')
    return render_template('admin/key_add.html', form=form)

@admin.route('/user/<user_id>/change_keyholder', methods=['POST'])
def change_is_keyholder(user_id):
    is_keyholder = request.form['keyholder'].lower() == 'true'
    user = User.query.get(user_id)
    user.is_keyholder = is_keyholder
    db.session.commit()
    flash("changed keyholder status for %s" % user.nick, 'success')
    return redirect_back(".users")

@admin.route('/user/<int:user_id>/change_admin', methods=['POST'])
def change_is_admin(user_id):
    is_admin = request.form['admin'].lower() == 'true'
    if g.user.id == user_id:
        raise abort(400, "can't change own admin status")
    user = User.query.get(user_id)
    user.is_admin = is_admin
    db.session.commit()
    flash("changed admin status for %s" % user.nick, 'success')
    return redirect_back(".users")

