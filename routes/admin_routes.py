from flask import Blueprint, render_template

from models.quote_model import list_recent_quote_predictions, quote_prediction_stats
from utils.decorators import admin_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin")
@admin_required
def admin_dashboard():
    stats = quote_prediction_stats()
    recent_quotes = list_recent_quote_predictions()
    return render_template("admin.html", stats=stats, recent_quotes=recent_quotes)
