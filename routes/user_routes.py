from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required
from models.user_model import find_user_by_id, mark_onboarding_seen
from models.quote_model import (
    add_project_file,
    add_project_message,
    approve_project_proposal,
    get_client_project,
    list_client_projects_for_user,
    list_notifications_for_user,
    list_saved_quotes_for_user,
    project_room_data,
    portal_stats_for_user,
    save_quote_to_portal,
)
from services.user_service import change_username, change_password

user_bp = Blueprint("user", __name__)

@user_bp.get("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    return render_template(
        "dashboard.html",
        portal_stats=portal_stats_for_user(user_id),
        saved_quotes=list_saved_quotes_for_user(user_id),
        client_projects=list_client_projects_for_user(user_id),
        notifications=list_notifications_for_user(user_id),
    )


@user_bp.post("/api/onboarding/complete")
@login_required
def complete_onboarding():
    mark_onboarding_seen(session["user_id"])
    return jsonify({"ok": True})


@user_bp.post("/api/quotes/save")
@login_required
def save_quote():
    data = request.get_json(silent=True) or {}
    prediction_id = data.get("prediction_id")
    try:
        prediction_id = int(prediction_id)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Run the ML prediction first."}), 400

    if not save_quote_to_portal(session["user_id"], prediction_id):
        return jsonify({"ok": False, "error": "Quote was not found for your account."}), 404

    return jsonify({"ok": True, "message": "Quote saved to your client portal."})


@user_bp.get("/dashboard/projects/<int:project_id>")
@login_required
def project_room(project_id):
    project = get_client_project(project_id, session["user_id"])
    if not project:
        flash("Project room was not found.", "error")
        return redirect(url_for("user.dashboard"))
    room = project_room_data(project_id)
    return render_template("project_room.html", project=project, room=room)


@user_bp.post("/dashboard/projects/<int:project_id>/message")
@login_required
def project_message(project_id):
    project = get_client_project(project_id, session["user_id"])
    if not project:
        flash("Project room was not found.", "error")
        return redirect(url_for("user.dashboard"))
    add_project_message(project_id, session["user_id"], request.form.get("body"))
    return redirect(url_for("user.project_room", project_id=project_id))


@user_bp.post("/dashboard/projects/<int:project_id>/file")
@login_required
def project_file(project_id):
    project = get_client_project(project_id, session["user_id"])
    if not project:
        flash("Project room was not found.", "error")
        return redirect(url_for("user.dashboard"))
    add_project_file(
        project_id,
        session["user_id"],
        request.form.get("label"),
        request.form.get("file_url"),
    )
    return redirect(url_for("user.project_room", project_id=project_id))


@user_bp.post("/dashboard/projects/<int:project_id>/approve")
@login_required
def project_approve(project_id):
    if approve_project_proposal(project_id, session["user_id"]):
        flash("Proposal approved.", "success")
    else:
        flash("Project room was not found.", "error")
    return redirect(url_for("user.project_room", project_id=project_id))


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
