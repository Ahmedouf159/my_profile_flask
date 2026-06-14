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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.commit()
    finally:
        conn.close()
