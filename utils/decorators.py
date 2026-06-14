from functools import wraps
from flask import session, redirect, url_for, flash
from models.user_model import find_user_by_id

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

def guest_only(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" in session:
            return redirect(url_for("user.dashboard"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        user = find_user_by_id(session["user_id"])
        if not user or not user["is_admin"]:
            flash("Admin access only.", "error")
            return redirect(url_for("user.dashboard"))

        return fn(*args, **kwargs)
    return wrapper
