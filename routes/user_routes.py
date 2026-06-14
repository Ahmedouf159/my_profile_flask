from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required
from models.user_model import find_user_by_id
from services.user_service import change_username, change_password

user_bp = Blueprint("user", __name__)

@user_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@user_bp.post("/api/secret-offer")
@login_required
def secret_offer():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()

    if code != current_app.config["SECRET_OFFER_CODE"]:
        return jsonify({"ok": False, "error": "Invalid secret code."}), 400

    return jsonify(
        {
            "ok": True,
            "offer": {
                "name": current_app.config["SECRET_OFFER_NAME"],
                "price": current_app.config["SECRET_OFFER_PRICE"],
                "includes": [
                    "3 page responsive website",
                    "Contact buttons and social links",
                    "Basic Flask dashboard",
                    "Delivery in 3-5 days",
                ],
            },
        }
    )

@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = find_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        ok1, msg1 = change_username(session["user_id"], request.form.get("username"))
        if msg1:
            flash(msg1, "success" if ok1 else "error")
            if not ok1:
                return redirect(url_for("user.profile"))

        ok2, msg2 = change_password(
            session["user_id"],
            request.form.get("new_password"),
            request.form.get("confirm_new_password"),
        )
        if msg2:
            flash(msg2, "success" if ok2 else "error")
            if not ok2:
                return redirect(url_for("user.profile"))

        return redirect(url_for("user.profile"))

    return render_template("profile.html", user=user)
