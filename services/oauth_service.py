import re
import secrets

from werkzeug.security import generate_password_hash

from models.user_model import (
    create_oauth_user,
    find_user_by_email,
    find_user_by_id,
    find_user_by_login,
    find_user_by_oauth,
    link_oauth_identity,
)


try:
    from authlib.integrations.flask_client import OAuth
except ImportError:
    OAuth = None


PROVIDERS = ("google", "facebook")
GOOGLE_CLIENT_ID_PATTERN = re.compile(r"^\d+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com$")
GOOGLE_CLIENT_SECRET_PATTERN = re.compile(r"^GOCSPX-[A-Za-z0-9_-]+$")
FACEBOOK_CLIENT_ID_PATTERN = re.compile(r"^\d+$")
FACEBOOK_CLIENT_SECRET_PATTERN = re.compile(r"^[A-Fa-f0-9]{32}$")


def init_oauth(app):
    app.extensions["oauth_available"] = OAuth is not None
    if OAuth is None:
        app.extensions["oauth"] = None
        return

    oauth = OAuth(app)
    app.extensions["oauth"] = oauth

    if is_provider_configured(app, "google"):
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if is_provider_configured(app, "facebook"):
        oauth.register(
            name="facebook",
            client_id=app.config["FACEBOOK_CLIENT_ID"],
            client_secret=app.config["FACEBOOK_CLIENT_SECRET"],
            access_token_url="https://graph.facebook.com/v19.0/oauth/access_token",
            authorize_url="https://www.facebook.com/v19.0/dialog/oauth",
            api_base_url="https://graph.facebook.com/v19.0/",
            client_kwargs={"scope": "email,public_profile"},
        )


def is_provider_configured(app, provider: str) -> bool:
    return oauth_config_issue(app, provider) is None


def oauth_config_issue(app, provider: str) -> str | None:
    if provider == "google":
        client_id = app.config.get("GOOGLE_CLIENT_ID", "")
        client_secret = app.config.get("GOOGLE_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return "Add the Google OAuth client ID and secret."
        if not GOOGLE_CLIENT_ID_PATTERN.match(client_id):
            return "Google OAuth client ID format looks wrong."
        if not GOOGLE_CLIENT_SECRET_PATTERN.match(client_secret):
            return "Google OAuth client secret format looks wrong."
        return None

    if provider == "facebook":
        client_id = app.config.get("FACEBOOK_CLIENT_ID", "")
        client_secret = app.config.get("FACEBOOK_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return "Add the Facebook app ID and app secret."
        if not FACEBOOK_CLIENT_ID_PATTERN.match(client_id):
            return "Facebook app ID format looks wrong."
        if not FACEBOOK_CLIENT_SECRET_PATTERN.match(client_secret):
            return "Facebook app secret format looks wrong."
        return None

    return "Unknown social login provider."


def social_login_status(app):
    available = app.extensions.get("oauth_available", False)
    return {
        provider: {
            "configured": available and is_provider_configured(app, provider),
            "missing_dependency": not available,
            "message": oauth_config_issue(app, provider),
        }
        for provider in PROVIDERS
    }


def normalize_google_profile(data):
    return {
        "subject": data.get("sub"),
        "email": (data.get("email") or "").strip().lower(),
        "name": (data.get("name") or data.get("given_name") or "google_user").strip(),
    }


def normalize_facebook_profile(data):
    return {
        "subject": data.get("id"),
        "email": (data.get("email") or "").strip().lower(),
        "name": (data.get("name") or "facebook_user").strip(),
    }


def _slug_username(value: str) -> str:
    username = "".join(char.lower() if char.isalnum() else "_" for char in value)
    username = "_".join(part for part in username.split("_") if part)
    return username[:24] or "social_user"


def _unique_username(base: str) -> str:
    username = _slug_username(base)
    candidate = username
    suffix = 1
    while find_user_by_login(candidate):
        suffix += 1
        candidate = f"{username[:24]}_{suffix}"
    return candidate


def login_or_create_oauth_user(provider: str, profile: dict):
    subject = profile.get("subject")
    email = profile.get("email")
    name = profile.get("name") or provider

    if not subject:
        return None, "The social login provider did not return an account id."
    if not email:
        return None, "The social login provider did not return an email address."

    user = find_user_by_oauth(provider, subject)
    if user:
        return user, "Welcome back!"

    user = find_user_by_email(email)
    if user:
        link_oauth_identity(user["id"], provider, subject)
        return find_user_by_id(user["id"]), "Social login connected."

    username = _unique_username(name)
    password_hash = generate_password_hash(secrets.token_urlsafe(32))
    user_id = create_oauth_user(username, email, password_hash, provider, subject)
    return find_user_by_id(user_id), "Account created with social login."
