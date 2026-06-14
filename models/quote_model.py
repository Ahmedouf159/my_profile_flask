import json

from models.db import get_db


def save_quote_prediction(user_id: int | None, payload: dict, prediction: dict) -> int:
    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO quote_predictions(
                user_id, project_type, pages, deadline, budget, features_json,
                package, price_min, price_max, days_min, days_max,
                success_score, risk, model_engine
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user_id,
                payload.get("projectType", "portfolio"),
                int(payload.get("pages", 3) or 3),
                payload.get("deadline", "normal"),
                payload.get("budget", "medium"),
                json.dumps(payload.get("features") or []),
                prediction["package"],
                prediction["price_min"],
                prediction["price_max"],
                prediction["days_min"],
                prediction["days_max"],
                prediction["success_score"],
                prediction["risk"],
                prediction["model_engine"],
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_recent_quote_predictions(limit: int = 12):
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT qp.*, u.username
            FROM quote_predictions qp
            LEFT JOIN users u ON u.id = qp.user_id
            ORDER BY qp.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def quote_prediction_stats():
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) AS count FROM quote_predictions").fetchone()["count"]
        summary = conn.execute(
            """
            SELECT
                COALESCE(ROUND(AVG(success_score)), 0) AS avg_success,
                COALESCE(ROUND(AVG(price_min)), 0) AS avg_price_min,
                COALESCE(ROUND(AVG(price_max)), 0) AS avg_price_max,
                COALESCE(ROUND(AVG(days_min)), 0) AS avg_days_min,
                COALESCE(ROUND(AVG(days_max)), 0) AS avg_days_max
            FROM quote_predictions
            """
        ).fetchone()

        def counts(column: str):
            rows = conn.execute(
                f"""
                SELECT {column} AS label, COUNT(*) AS count
                FROM quote_predictions
                GROUP BY {column}
                ORDER BY count DESC, label ASC
                """
            ).fetchall()
            return [{"label": row["label"], "count": row["count"]} for row in rows]

        return {
            "total": total,
            "avg_success": int(summary["avg_success"] or 0),
            "avg_price_min": int(summary["avg_price_min"] or 0),
            "avg_price_max": int(summary["avg_price_max"] or 0),
            "avg_days_min": int(summary["avg_days_min"] or 0),
            "avg_days_max": int(summary["avg_days_max"] or 0),
            "by_type": counts("project_type"),
            "by_risk": counts("risk"),
            "by_package": counts("package"),
        }
    finally:
        conn.close()
