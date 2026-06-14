import json

from models.db import get_db


def _lead_score(payload: dict, prediction: dict) -> int:
    score = int(prediction.get("success_score", 50) or 50)
    budget = payload.get("budget", "medium")
    deadline = payload.get("deadline", "normal")
    features = payload.get("features") or []

    score += {"flexible": 15, "high": 12, "medium": 5, "low": -8}.get(budget, 0)
    score += {"normal": 8, "fast": 0, "urgent": -10}.get(deadline, 0)
    score += min(len(features) * 3, 12)
    if prediction.get("risk") == "High":
        score -= 12
    elif prediction.get("risk") == "Low":
        score += 8

    return max(1, min(score, 100))


def save_quote_prediction(user_id: int | None, payload: dict, prediction: dict) -> int:
    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO quote_predictions(
                user_id, project_type, pages, deadline, budget, features_json,
                package, price_min, price_max, days_min, days_max,
                success_score, risk, model_engine, lead_score
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                _lead_score(payload, prediction),
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


def list_saved_quotes_for_user(user_id: int, limit: int = 8):
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT *
            FROM quote_predictions
            WHERE user_id=? AND is_saved=1
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()


def list_client_projects_for_user(user_id: int, limit: int = 8):
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT *
            FROM client_projects
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()


def list_notifications_for_user(user_id: int, limit: int = 6):
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT *
            FROM notifications
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()


def save_quote_to_portal(user_id: int, prediction_id: int) -> bool:
    conn = get_db()
    try:
        quote = conn.execute(
            "SELECT * FROM quote_predictions WHERE id=? AND user_id=?",
            (prediction_id, user_id),
        ).fetchone()
        if not quote:
            return False

        conn.execute(
            """
            UPDATE quote_predictions
            SET is_saved=1, lead_status=CASE WHEN lead_status='new' THEN 'saved' ELSE lead_status END
            WHERE id=? AND user_id=?
            """,
            (prediction_id, user_id),
        )

        existing_project = conn.execute(
            "SELECT id FROM client_projects WHERE quote_prediction_id=? AND user_id=?",
            (prediction_id, user_id),
        ).fetchone()
        if not existing_project:
            title = f"{quote['project_type'].title()} {quote['package']} Project"
            summary = (
                f"{quote['package']} package, ${quote['price_min']}-${quote['price_max']}, "
                f"{quote['days_min']}-{quote['days_max']} days, {quote['risk']} risk."
            )
            cursor = conn.execute(
                """
                INSERT INTO client_projects(user_id, quote_prediction_id, title, project_type, summary)
                VALUES(?,?,?,?,?)
                """,
                (user_id, prediction_id, title, quote["project_type"], summary),
            )
            project_id = cursor.lastrowid
            conn.executemany(
                """
                INSERT INTO project_milestones(project_id, title, status, sort_order)
                VALUES(?,?,?,?)
                """,
                [
                    (project_id, "Brief received", "done", 1),
                    (project_id, "Proposal approval", "todo", 2),
                    (project_id, "Design and build", "todo", 3),
                    (project_id, "Testing and delivery", "todo", 4),
                ],
            )

        conn.execute(
            """
            INSERT INTO notifications(user_id, title, body)
            VALUES(?,?,?)
            """,
            (
                user_id,
                "Quote saved to your portal",
                "Your project estimate is now available in Saved Quotes and Project Tracker.",
            ),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_client_project(project_id: int, user_id: int | None = None, is_admin: bool = False):
    conn = get_db()
    try:
        if is_admin:
            return conn.execute(
                """
                SELECT cp.*, u.username, u.email, qp.package, qp.price_min, qp.price_max, qp.lead_score
                FROM client_projects cp
                JOIN users u ON u.id = cp.user_id
                LEFT JOIN quote_predictions qp ON qp.id = cp.quote_prediction_id
                WHERE cp.id=?
                """,
                (project_id,),
            ).fetchone()
        return conn.execute(
            """
            SELECT cp.*, qp.package, qp.price_min, qp.price_max, qp.lead_score
            FROM client_projects cp
            LEFT JOIN quote_predictions qp ON qp.id = cp.quote_prediction_id
            WHERE cp.id=? AND cp.user_id=?
            """,
            (project_id, user_id),
        ).fetchone()
    finally:
        conn.close()


def project_room_data(project_id: int):
    conn = get_db()
    try:
        messages = conn.execute(
            """
            SELECT pm.*, u.username
            FROM project_messages pm
            JOIN users u ON u.id = pm.user_id
            WHERE pm.project_id=?
            ORDER BY pm.id ASC
            """,
            (project_id,),
        ).fetchall()
        files = conn.execute(
            "SELECT * FROM project_files WHERE project_id=? ORDER BY id DESC",
            (project_id,),
        ).fetchall()
        milestones = conn.execute(
            "SELECT * FROM project_milestones WHERE project_id=? ORDER BY sort_order ASC, id ASC",
            (project_id,),
        ).fetchall()
        return {"messages": messages, "files": files, "milestones": milestones}
    finally:
        conn.close()


def add_project_message(project_id: int, user_id: int, body: str, is_admin: bool = False):
    body = (body or "").strip()
    if not body:
        return False
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO project_messages(project_id, user_id, body, is_admin) VALUES(?,?,?,?)",
            (project_id, user_id, body, 1 if is_admin else 0),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_project_file(project_id: int, user_id: int, label: str, file_url: str):
    label = (label or "").strip()
    file_url = (file_url or "").strip()
    if not label or not file_url:
        return False
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO project_files(project_id, user_id, label, file_url) VALUES(?,?,?,?)",
            (project_id, user_id, label, file_url),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def approve_project_proposal(project_id: int, user_id: int):
    conn = get_db()
    try:
        project = conn.execute(
            "SELECT id FROM client_projects WHERE id=? AND user_id=?",
            (project_id, user_id),
        ).fetchone()
        if not project:
            return False
        conn.execute(
            """
            UPDATE client_projects
            SET status='Proposal Approved', next_step='Ahmed will prepare the build plan.', updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (project_id,),
        )
        conn.execute(
            "UPDATE project_milestones SET status='done' WHERE project_id=? AND title='Proposal approval'",
            (project_id,),
        )
        conn.execute(
            "INSERT INTO notifications(user_id, title, body) VALUES(?,?,?)",
            (user_id, "Proposal approved", "Your project room has been updated with the approved proposal status."),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_all_client_projects(limit: int = 30):
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT cp.*, u.username, u.email, qp.lead_score
            FROM client_projects cp
            JOIN users u ON u.id = cp.user_id
            LEFT JOIN quote_predictions qp ON qp.id = cp.quote_prediction_id
            ORDER BY cp.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def ai_reply_for_lead(lead) -> str:
    project = lead["project_type"].title()
    package = lead["package"]
    price = f"${lead['price_min']} - ${lead['price_max']}"
    return (
        f"Hi {lead['username'] or 'there'}, thanks for sharing your {project} idea. "
        f"Based on the {package} estimate, the expected range is {price}. "
        "I recommend confirming the core pages, must-have features, and deadline first, "
        "then I can send a clean proposal with milestones."
    )


def list_pricing_packages():
    return [
        {"name": "Starter", "price": "$25+", "fit": "Landing page or simple portfolio", "features": ["1-3 pages", "Responsive UI", "Contact links"]},
        {"name": "Pro", "price": "$75+", "fit": "Business site with dashboard basics", "features": ["5 pages", "Forms", "Database-ready flow"]},
        {"name": "Portal", "price": "$150+", "fit": "Client portal or admin CRM", "features": ["Auth", "Saved quotes", "Admin dashboard"]},
        {"name": "Automation", "price": "$50+", "fit": "Python scripts and workflow tools", "features": ["File tools", "Reports", "Repeatable scripts"]},
    ]


def list_testimonials():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM testimonials WHERE is_published=1 ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()


def list_case_studies():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM case_studies WHERE is_published=1 ORDER BY id DESC"
        ).fetchall()
    finally:
        conn.close()


def get_case_study(slug: str):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM case_studies WHERE slug=? AND is_published=1",
            (slug,),
        ).fetchone()
    finally:
        conn.close()


def list_admin_leads(limit: int = 20):
    conn = get_db()
    try:
        return conn.execute(
            """
            SELECT qp.*, u.username, u.email
            FROM quote_predictions qp
            LEFT JOIN users u ON u.id = qp.user_id
            WHERE qp.user_id IS NOT NULL
            ORDER BY qp.is_saved DESC, qp.lead_score DESC, qp.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def portal_stats_for_user(user_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT
                SUM(CASE WHEN is_saved=1 THEN 1 ELSE 0 END) AS saved_quotes,
                COUNT(*) AS total_predictions,
                COALESCE(MAX(lead_score), 0) AS best_score
            FROM quote_predictions
            WHERE user_id=?
            """,
            (user_id,),
        ).fetchone()
        projects = conn.execute(
            "SELECT COUNT(*) AS count FROM client_projects WHERE user_id=?",
            (user_id,),
        ).fetchone()["count"]
        unread = conn.execute(
            "SELECT COUNT(*) AS count FROM notifications WHERE user_id=? AND is_read=0",
            (user_id,),
        ).fetchone()["count"]
        return {
            "saved_quotes": int(row["saved_quotes"] or 0),
            "total_predictions": int(row["total_predictions"] or 0),
            "best_score": int(row["best_score"] or 0),
            "projects": int(projects or 0),
            "unread": int(unread or 0),
        }
    finally:
        conn.close()


def quote_prediction_stats():
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) AS count FROM quote_predictions").fetchone()["count"]
        saved = conn.execute("SELECT COUNT(*) AS count FROM quote_predictions WHERE is_saved=1").fetchone()["count"]
        active_leads = conn.execute(
            "SELECT COUNT(*) AS count FROM quote_predictions WHERE user_id IS NOT NULL"
        ).fetchone()["count"]
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
            "saved": saved,
            "active_leads": active_leads,
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
