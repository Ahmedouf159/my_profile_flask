import os
import sqlite3

from flask import current_app, has_app_context

from config.settings import DATABASE, INSTANCE_DIR


def get_db(database_path: str | None = None):
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    if database_path is None and has_app_context():
        database_path = current_app.config["DATABASE"]
    conn = sqlite3.connect(database_path or DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _column_names(conn):
    return {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}


def init_db(database_path: str | None = None):
    conn = get_db(database_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                theme TEXT NOT NULL DEFAULT 'system',
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if "theme" not in _column_names(conn):
            conn.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'system'")

        columns = _column_names(conn)
        if "oauth_provider" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT")
        if "oauth_subject" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN oauth_subject TEXT")
        if "is_admin" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        if "onboarding_seen" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN onboarding_seen INTEGER NOT NULL DEFAULT 0")

        admin_count = conn.execute("SELECT COUNT(*) AS count FROM users WHERE is_admin=1").fetchone()["count"]
        first_user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        if admin_count == 0 and first_user:
            conn.execute("UPDATE users SET is_admin=1 WHERE id=?", (first_user["id"],))

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quote_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                project_type TEXT NOT NULL,
                pages INTEGER NOT NULL,
                deadline TEXT NOT NULL,
                budget TEXT NOT NULL,
                features_json TEXT NOT NULL,
                package TEXT NOT NULL,
                price_min INTEGER NOT NULL,
                price_max INTEGER NOT NULL,
                days_min INTEGER NOT NULL,
                days_max INTEGER NOT NULL,
                success_score INTEGER NOT NULL,
                risk TEXT NOT NULL,
                model_engine TEXT NOT NULL,
                is_saved INTEGER NOT NULL DEFAULT 0,
                lead_status TEXT NOT NULL DEFAULT 'new',
                lead_score INTEGER NOT NULL DEFAULT 0,
                admin_note TEXT NOT NULL DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        quote_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(quote_predictions)").fetchall()
        }
        if "is_saved" not in quote_columns:
            conn.execute("ALTER TABLE quote_predictions ADD COLUMN is_saved INTEGER NOT NULL DEFAULT 0")
        if "lead_status" not in quote_columns:
            conn.execute("ALTER TABLE quote_predictions ADD COLUMN lead_status TEXT NOT NULL DEFAULT 'new'")
        if "lead_score" not in quote_columns:
            conn.execute("ALTER TABLE quote_predictions ADD COLUMN lead_score INTEGER NOT NULL DEFAULT 0")
        if "admin_note" not in quote_columns:
            conn.execute("ALTER TABLE quote_predictions ADD COLUMN admin_note TEXT NOT NULL DEFAULT ''")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quote_prediction_id INTEGER,
                title TEXT NOT NULL,
                project_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Discovery',
                summary TEXT NOT NULL DEFAULT '',
                next_step TEXT NOT NULL DEFAULT 'Review the quote and confirm scope',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(quote_prediction_id) REFERENCES quote_predictions(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES client_projects(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                file_url TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES client_projects(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                sort_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(project_id) REFERENCES client_projects(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS testimonials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                role TEXT NOT NULL,
                quote TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 5,
                is_published INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_studies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                challenge TEXT NOT NULL,
                solution TEXT NOT NULL,
                result TEXT NOT NULL,
                stack TEXT NOT NULL,
                is_published INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if conn.execute("SELECT COUNT(*) AS count FROM testimonials").fetchone()["count"] == 0:
            conn.executemany(
                """
                INSERT INTO testimonials(client_name, role, quote, rating)
                VALUES(?,?,?,?)
                """,
                [
                    ("Demo Client", "Startup Founder", "Ahmed turned a rough idea into a clear Flask dashboard flow.", 5),
                    ("Portfolio Lead", "Business Owner", "The quote builder made the project scope easy to understand.", 5),
                    ("Automation User", "Operations", "Small automation tools saved hours of repeated manual work.", 4),
                ],
            )

        if conn.execute("SELECT COUNT(*) AS count FROM case_studies").fetchone()["count"] == 0:
            conn.executemany(
                """
                INSERT INTO case_studies(slug, title, challenge, solution, result, stack)
                VALUES(?,?,?,?,?,?)
                """,
                [
                    (
                        "portfolio-auth-system",
                        "Portfolio Auth System",
                        "A simple portfolio needed real account features without becoming messy.",
                        "Built Flask blueprints, SQLite models, CSRF protection, profile editing, and tests.",
                        "The site became a working full-stack demo with protected routes and admin features.",
                        "Flask, SQLite, Pytest, HTML, CSS, JavaScript",
                    ),
                    (
                        "smart-quote-builder",
                        "Smart Quote Builder",
                        "Visitors needed a faster way to understand budget, timeline, and project risk.",
                        "Added ML-style predictions, roadmap generation, PDF proposals, and saved quotes.",
                        "Quotes now become leads, client portal projects, and admin CRM records.",
                        "Flask, NumPy, SQLite, JavaScript",
                    ),
                ],
            )

        conn.commit()
    finally:
        conn.close()
