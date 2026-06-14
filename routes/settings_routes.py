from flask import Blueprint, render_template, jsonify, request, session
from models.user_model import find_user_by_id
from utils.decorators import login_required
from services.theme_service import save_theme

settings_bp = Blueprint("settings", __name__)

@settings_bp.get("/settings")
@login_required
def settings():
    user = find_user_by_id(session["user_id"])
    return render_template("settings.html", theme=user["theme"] if user else "system")

@settings_bp.post("/api/theme")
@login_required
def api_theme():
    data = request.get_json(silent=True) or {}
    ok, result = save_theme(session["user_id"], data.get("theme"))
    if not ok:
        return jsonify({"ok": False, "error": result}), 400

    # store preference in session (pref), JS will apply effective theme
    session["theme"] = result
    return jsonify({"ok": True, "theme": result})
