from urlparse import urlparse, urljoin
from functools import wraps
from flask import g, redirect, url_for, abort, request

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_authenticated():
            return redirect(url_for('user.login', next=request.url))
        if not g.user.is_admin:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def keyholder_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_authenticated():
            return redirect(url_for('user.login', next=request.url))
        if not g.user.is_keyholder and not g.user.is_keymanager:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
