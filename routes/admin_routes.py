from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.quote_model import (
    add_project_message,
    ai_reply_for_lead,
    get_client_project,
    list_admin_leads,
    list_all_client_projects,
    list_recent_quote_predictions,
    project_room_data,
    quote_prediction_stats,
)
from utils.decorators import admin_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin")
@admin_required
def admin_dashboard():
    stats = quote_prediction_stats()
    recent_quotes = list_recent_quote_predictions()
    leads = list_admin_leads()
    projects = list_all_client_projects()
    ai_replies = {lead["id"]: ai_reply_for_lead(lead) for lead in leads}
    return render_template(
        "admin.html",
        stats=stats,
        recent_quotes=recent_quotes,
        leads=leads,
        projects=projects,
        ai_replies=ai_replies,
    )


@admin_bp.get("/admin/projects/<int:project_id>")
@admin_required
def admin_project_room(project_id):
    project = get_client_project(project_id, is_admin=True)
    if not project:
        flash("Project room was not found.", "error")
        return redirect(url_for("admin.admin_dashboard"))
    room = project_room_data(project_id)
    return render_template("project_room.html", project=project, room=room, admin_view=True)


@admin_bp.post("/admin/projects/<int:project_id>/message")
@admin_required
def admin_project_message(project_id):
    project = get_client_project(project_id, is_admin=True)
    if not project:
        flash("Project room was not found.", "error")
        return redirect(url_for("admin.admin_dashboard"))
    add_project_message(project_id, session["user_id"], request.form.get("body"), is_admin=True)
    return redirect(url_for("admin.admin_project_room", project_id=project_id))
