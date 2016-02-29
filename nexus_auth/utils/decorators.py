from flask import flash, redirect
from flask.ext.login import current_user
from functools import wraps


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            flash("You are unable to access that.", "danger")
            return redirect("/")
        else:
            return func(*args, **kwargs)

    return decorated_view


def services_access_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.has_services_access():
            flash('You are not in any group with services access.')
            return redirect('/')
        else:
            return func(*args, **kwargs)

    return decorated_view