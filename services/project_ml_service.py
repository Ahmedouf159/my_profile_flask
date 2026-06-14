from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import pandas as pd


PROJECT_TYPES = ("portfolio", "business", "store", "dashboard")
DEADLINES = ("normal", "fast", "urgent")
BUDGETS = ("low", "medium", "high", "flexible")
FEATURES = ("contact", "auth", "socialAuth", "admin", "database", "payments")


@dataclass(frozen=True)
class ProjectPrediction:
    package: str
    price_min: int
    price_max: int
    days_min: int
    days_max: int
    success_score: int
    risk: str
    model_engine: str
    advice: list[str]


class _NumpyMultiRegression:
    def __init__(self) -> None:
        self.coefficients: np.ndarray | None = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.coefficients = np.linalg.lstsq(x, y, rcond=None)[0]

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.coefficients is None:
            raise RuntimeError("Model is not fitted.")
        return x @ self.coefficients


def _project_base(project_type: str) -> tuple[int, int, int, int, int]:
    values = {
        "portfolio": (35, 60, 2, 4, 88),
        "business": (60, 100, 3, 5, 82),
        "store": (90, 160, 5, 8, 76),
        "dashboard": (110, 220, 6, 10, 72),
    }
    return values[project_type]


def _feature_costs(features: set[str]) -> tuple[int, int, int, int]:
    costs = {
        "contact": (10, 20, 0, 2),
        "auth": (25, 45, 2, -2),
        "socialAuth": (30, 60, 2, -4),
        "admin": (45, 90, 3, -6),
        "database": (25, 55, 2, -3),
        "payments": (45, 100, 3, -8),
    }
    min_cost = max_cost = days = risk_delta = 0
    for feature in features:
        feature_min, feature_max, feature_days, feature_risk = costs[feature]
        min_cost += feature_min
        max_cost += feature_max
        days += feature_days
        risk_delta += feature_risk
    return min_cost, max_cost, days, risk_delta


def _normalize_features(project_type: str, features: set[str]) -> set[str]:
    normalized = set(features)
    if "socialAuth" in normalized:
        normalized.add("auth")
    if project_type in {"store", "dashboard"}:
        normalized.add("database")
    return normalized


def _realistic_project_row(
    project_type: str,
    pages: int,
    deadline: str,
    budget: str,
    selected_features: set[str],
) -> dict:
    features = _normalize_features(project_type, selected_features)
    base_min, base_max, days_min, days_max, base_success = _project_base(project_type)
    feature_min, feature_max, feature_days, feature_risk = _feature_costs(features)

    price_min = base_min + max(pages - 1, 0) * 8 + feature_min
    price_max = base_max + max(pages - 1, 0) * 14 + feature_max
    days_min += max((pages - 3 + 1) // 2, 0)
    days_max += max((pages - 3 + 1) // 2, 0) + feature_days

    success = base_success + feature_risk
    success -= max(pages - 3, 0) * 2

    if deadline == "fast":
        price_min = round(price_min * 1.18)
        price_max = round(price_max * 1.25)
        days_min = max(1, days_min - 1)
        days_max = max(days_min + 1, days_max - 2)
        success -= 6
    elif deadline == "urgent":
        price_min = round(price_min * 1.35)
        price_max = round(price_max * 1.5)
        days_min = max(1, days_min - 2)
        days_max = max(days_min + 1, days_max - 3)
        success -= 14

    if budget == "low":
        success -= 12 if price_min > 80 else 4
    elif budget == "medium":
        success += 5 if price_min <= 180 else -3
    elif budget == "high":
        success += 9
    elif budget == "flexible":
        success += 12

    if "contact" in features:
        success += 2
    if "database" in features and project_type in {"store", "dashboard"}:
        success += 3

    return {
        "project_type": project_type,
        "pages": pages,
        "deadline": deadline,
        "budget": budget,
        "contact": int("contact" in features),
        "auth": int("auth" in features),
        "socialAuth": int("socialAuth" in features),
        "admin": int("admin" in features),
        "database": int("database" in features),
        "payments": int("payments" in features),
        "price_min": price_min,
        "price_max": price_max,
        "days_min": days_min,
        "days_max": days_max,
        "success_score": max(25, min(96, round(success))),
    }


def _training_data() -> pd.DataFrame:
    rows = []
    feature_sets = []
    for mask in range(2 ** len(FEATURES)):
        selected = {feature for index, feature in enumerate(FEATURES) if mask & (1 << index)}
        if "socialAuth" in selected and "auth" not in selected:
            selected.add("auth")
        feature_sets.append(selected)

    for project_type, pages, deadline, budget, features in itertools.product(
        PROJECT_TYPES,
        (1, 3, 5, 8),
        DEADLINES,
        BUDGETS,
        feature_sets,
    ):
        rows.append(_realistic_project_row(project_type, pages, deadline, budget, features))
    return pd.DataFrame(rows)


def _feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    encoded = pd.get_dummies(df[["project_type", "deadline", "budget"]], dtype=float)
    numeric = df[["pages", *FEATURES]].astype(float)
    return pd.concat([numeric, encoded], axis=1)


def _fit_model() -> tuple[object, list[str], str]:
    df = _training_data()
    x_frame = _feature_frame(df)
    y = df[["price_min", "price_max", "days_min", "days_max", "success_score"]].to_numpy(dtype=float)

    try:
        from sklearn.linear_model import Ridge
        from sklearn.multioutput import MultiOutputRegressor

        model = MultiOutputRegressor(Ridge(alpha=0.8))
        model.fit(x_frame.to_numpy(dtype=float), y)
        return model, list(x_frame.columns), "scikit-learn Ridge"
    except ImportError:
        x = np.c_[np.ones(len(x_frame)), x_frame.to_numpy(dtype=float)]
        model = _NumpyMultiRegression()
        model.fit(x, y)
        return model, list(x_frame.columns), "NumPy linear regression"


_MODEL, _FEATURE_COLUMNS, _MODEL_ENGINE = _fit_model()


def _encode_input(payload: dict) -> np.ndarray:
    project_type = payload.get("projectType", "portfolio")
    deadline = payload.get("deadline", "normal")
    budget = payload.get("budget", "medium")

    if project_type not in PROJECT_TYPES:
        project_type = "portfolio"
    if deadline not in DEADLINES:
        deadline = "normal"
    if budget not in BUDGETS:
        budget = "medium"

    pages = int(payload.get("pages", 3) or 3)
    pages = max(1, min(pages, 12))
    features = set(payload.get("features") or [])
    features = _normalize_features(project_type, features.intersection(FEATURES))

    row = {
        "pages": pages,
        **{feature: int(feature in features) for feature in FEATURES},
        **{f"project_type_{value}": int(value == project_type) for value in PROJECT_TYPES},
        **{f"deadline_{value}": int(value == deadline) for value in DEADLINES},
        **{f"budget_{value}": int(value == budget) for value in BUDGETS},
    }
    values = [float(row.get(column, 0)) for column in _FEATURE_COLUMNS]
    if isinstance(_MODEL, _NumpyMultiRegression):
        values = [1.0, *values]
    return np.array([values], dtype=float)


def _package_for(price_max: int, success_score: int) -> str:
    if price_max >= 220 or success_score < 58:
        return "Advanced"
    if price_max >= 110:
        return "Pro"
    return "Starter"


def _risk_for(success_score: int) -> str:
    if success_score >= 78:
        return "Low"
    if success_score >= 58:
        return "Medium"
    return "High"


def _advice(payload: dict, success_score: int, risk: str) -> list[str]:
    features = set(payload.get("features") or [])
    deadline = payload.get("deadline", "normal")
    budget = payload.get("budget", "medium")
    project_type = payload.get("projectType", "portfolio")

    tips = []
    if risk == "High":
        tips.append("Reduce optional features or choose a normal deadline before starting.")
    if deadline == "urgent":
        tips.append("Urgent delivery increases risk; split the project into version 1 and version 2.")
    if "payments" in features and "database" not in features:
        tips.append("Payment work should include a database for orders and records.")
    if "socialAuth" in features:
        tips.append("Start with normal login first if Google/Facebook app approval slows you down.")
    if budget == "low" and project_type in {"store", "dashboard"}:
        tips.append("For this budget, start with a smaller MVP and add advanced screens later.")
    if success_score >= 78:
        tips.append("This project shape is realistic and ready for a clean first version.")

    return tips[:3]


def predict_project_success(payload: dict) -> ProjectPrediction:
    x = _encode_input(payload)
    raw = _MODEL.predict(x)[0]
    price_min, price_max, days_min, days_max, success_score = raw

    price_min = max(25, round(float(price_min) / 5) * 5)
    price_max = max(price_min + 20, round(float(price_max) / 5) * 5)
    days_min = max(1, round(float(days_min)))
    days_max = max(days_min + 1, round(float(days_max)))
    success_score = max(25, min(96, round(float(success_score))))
    risk = _risk_for(success_score)

    return ProjectPrediction(
        package=_package_for(price_max, success_score),
        price_min=price_min,
        price_max=price_max,
        days_min=days_min,
        days_max=days_max,
        success_score=success_score,
        risk=risk,
        model_engine=_MODEL_ENGINE,
        advice=_advice(payload, success_score, risk),
    )
