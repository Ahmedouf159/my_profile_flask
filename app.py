from __future__ import annotations

import os
import secrets
from functools import wraps
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from config import settings
from models.db import init_db
from models.user_model import find_user_by_id
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.ml_routes import ml_bp
from routes.page_routes import page_bp
from routes.settings_routes import settings_bp
from routes.user_routes import user_bp
from services.oauth_service import init_oauth, social_login_status


def _load_config(app: Flask) -> None:
    app.config.from_object(settings)
    app.config.from_prefixed_env()

    if app.config.get("SECRET_KEY") in (None, "", settings.DEV_SECRET_KEY):
        if app.config.get("ENVIRONMENT") == "production":
            raise RuntimeError("Set FLASK_SECRET_KEY before running in production.")
        app.config["SECRET_KEY"] = settings.DEV_SECRET_KEY


def _install_csrf(app: Flask) -> None:
    def csrf_token() -> str:
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    @app.before_request
    def protect_mutating_requests():
        if not app.config.get("CSRF_ENABLED", True):
            return None
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None

        expected = session.get("_csrf_token")
        supplied = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        if not expected or not supplied or not secrets.compare_digest(expected, supplied):
            abort(400)
        return None
    
    @app.context_processor
    def inject_csrf():
        return {"csrf_token": csrf_token}


def _install_template_context(app: Flask) -> None:
    @app.context_processor
    def inject_user():
        user = None
        user_id = session.get("user_id")
        if user_id:
            row = find_user_by_id(user_id)
            if row:
                user = {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "theme": row["theme"],
                    "is_admin": bool(row["is_admin"]),
                }

        contact_email = app.config["CONTACT_EMAIL"]
        contact_params = urlencode(
            {
                "view": "cm",
                "fs": "1",
                "to": contact_email,
                "su": "Portfolio project request",
                "body": "Hi Ahmed,\n\nI visited your portfolio and I would like to talk about a project.",
            }
        )

        return {
            "current_user": user,
            "avatar_letter": (user["username"][:1].lower() if user else None),
            "contact_email": contact_email,
            "contact_url": f"https://mail.google.com/mail/?{contact_params}",
            "brand_name": app.config["BRAND_NAME"],
            "youtube_handle": app.config["YOUTUBE_HANDLE"],
            "youtube_url": app.config["YOUTUBE_URL"],
            "github_url": app.config["GITHUB_URL"],
            "site_url": app.config["SITE_URL"],
            "social_login": social_login_status(app),
        }


def _install_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
        return response


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    _load_config(app)

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    init_db(app.config["DATABASE"])

    init_oauth(app)
    _install_csrf(app)
    _install_template_context(app)
    _install_security_headers(app)

    app.register_blueprint(page_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(admin_bp)

    @app.get("/blog")
    def blog():
        abort(404)

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": app.config["BRAND_NAME"]})

    @app.get("/robots.txt")
    def robots_txt():
        body = "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                f"Sitemap: {app.config['SITE_URL']}/sitemap.xml",
                "",
            ]
        )
        return Response(body, mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap_xml():
        paths = [
            url_for("pages.index"),
            url_for("pages.about"),
            url_for("pages.services"),
            url_for("pages.quote"),
            url_for("pages.projects"),
            url_for("auth.login"),
            url_for("auth.signup"),
        ]
        urls = "\n".join(
            f"  <url><loc>{app.config['SITE_URL']}{path}</loc></url>" for path in paths
        )
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""
        return Response(body, mimetype="application/xml")

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(400)
    def bad_request(_error):
        flash("Your form expired. Please try again.", "error")
        return redirect(request.referrer or url_for("pages.index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
