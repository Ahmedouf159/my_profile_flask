from dataclasses import asdict

from flask import Blueprint, jsonify, request, session

from models.quote_model import save_quote_prediction
from services.project_ml_service import predict_project_success


ml_bp = Blueprint("ml", __name__)


@ml_bp.post("/api/project-prediction")
def project_prediction():
    payload = request.get_json(silent=True) or {}
    prediction = predict_project_success(payload)
    prediction_data = asdict(prediction)
    prediction_id = save_quote_prediction(session.get("user_id"), payload, prediction_data)
    return jsonify({"ok": True, "prediction": prediction_data, "prediction_id": prediction_id})
