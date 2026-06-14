from time import time

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from services.auth_service import login_user, signup_user
from services.oauth_service import (
    login_or_create_oauth_user,
    normalize_facebook_profile,
    normalize_google_profile,
)
from utils.decorators import guest_only

auth_bp = Blueprint("auth", __name__)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


def _login_locked() -> bool:
    lock_until = session.get("login_lock_until", 0)
    return lock_until > time()


def _record_failed_login() -> None:
    attempts = session.get("login_attempts", 0) + 1
    session["login_attempts"] = attempts
    if attempts >= MAX_LOGIN_ATTEMPTS:
        session["login_lock_until"] = time() + LOCKOUT_SECONDS
        session["login_attempts"] = 0


@auth_bp.route("/signup", methods=["GET", "POST"])
@guest_only
def signup():
    if request.method == "POST":
        ok, msg = signup_user(
            request.form.get("username"),
            request.form.get("email"),
            request.form.get("password"),
            request.form.get("confirm_password"),
        )
        flash(msg, "success" if ok else "error")
        return redirect(url_for("auth.login" if ok else "auth.signup"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@guest_only
def login():
    if request.method == "POST":
        if _login_locked():
            flash("Too many login attempts. Try again in a minute.", "error")
            return redirect(url_for("auth.login"))

        user, msg = login_user(
            request.form.get("identity"),
            request.form.get("password"),
        )
        if not user:
            _record_failed_login()
            flash(msg, "error")
            return redirect(url_for("auth.login"))

        session.clear()
        session["user_id"] = user["id"]
        session.permanent = request.form.get("remember") == "on"

        return redirect(url_for("user.dashboard"))

    return render_template("login.html")


@auth_bp.get("/auth/<provider>")
@guest_only
def oauth_login(provider):
    oauth = current_app.extensions.get("oauth")
    client = oauth.create_client(provider) if oauth else None
    if provider not in {"google", "facebook"} or client is None:
        flash(f"{provider.title()} login is not configured yet.", "warning")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.oauth_callback", provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)


@auth_bp.get("/auth/<provider>/callback")
@guest_only
def oauth_callback(provider):
    oauth = current_app.extensions.get("oauth")
    client = oauth.create_client(provider) if oauth else None
    if provider not in {"google", "facebook"} or client is None:
        flash(f"{provider.title()} login is not configured yet.", "warning")
        return redirect(url_for("auth.login"))

    try:
        client.authorize_access_token()
        if provider == "google":
            profile = normalize_google_profile(client.get("https://openidconnect.googleapis.com/v1/userinfo").json())
        else:
            profile = normalize_facebook_profile(client.get("me?fields=id,name,email").json())
    except Exception:
        flash(f"{provider.title()} login failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    user, msg = login_or_create_oauth_user(provider, profile)
    if not user:
        flash(msg, "error")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True
    flash(msg, "success")
    return redirect(url_for("user.dashboard"))


@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("pages.index"))
