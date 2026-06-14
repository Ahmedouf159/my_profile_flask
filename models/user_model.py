from models.db import get_db


def create_user(username: str, email: str, password_hash: str):
    conn = get_db()
    try:
        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        conn.execute(
            "INSERT INTO users(username, email, password_hash, theme, is_admin) VALUES(?,?,?,?,?)",
            (username, email, password_hash, "system", 1 if user_count == 0 else 0),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_oauth_user(username: str, email: str, password_hash: str, provider: str, subject: str):
    conn = get_db()
    try:
        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        cursor = conn.execute(
            """
            INSERT INTO users(username, email, password_hash, theme, oauth_provider, oauth_subject, is_admin)
            VALUES(?,?,?,?,?,?,?)
            """,
            (username, email, password_hash, "system", provider, subject, 1 if user_count == 0 else 0),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def find_user_by_login(login_id: str):
    login_id = (login_id or "").strip().lower()
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE lower(email)=? OR lower(username)=?",
            (login_id, login_id),
        ).fetchone()
    finally:
        conn.close()


def find_user_by_email(email: str):
    email = (email or "").strip().lower()
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE lower(email)=?", (email,)).fetchone()
    finally:
        conn.close()


def find_user_by_oauth(provider: str, subject: str):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE oauth_provider=? AND oauth_subject=?",
            (provider, subject),
        ).fetchone()
    finally:
        conn.close()


def find_user_by_id(user_id: int):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    finally:
        conn.close()


def link_oauth_identity(user_id: int, provider: str, subject: str):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET oauth_provider=?, oauth_subject=? WHERE id=?",
            (provider, subject, user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_username(user_id: int, new_username: str):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_password_hash(user_id: int, new_hash: str):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_theme(user_id: int, theme: str):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_onboarding_seen(user_id: int):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET onboarding_seen=1 WHERE id=?", (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
