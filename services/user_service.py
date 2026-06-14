import sqlite3
from werkzeug.security import generate_password_hash
from utils.validators import is_valid_username, is_valid_password
from models.user_model import update_username, update_password_hash

def change_username(user_id: int, new_username: str):
    new_username = (new_username or "").strip()
    if not new_username:
        return True, None  # no change

    if not is_valid_username(new_username):
        return False, "Username must be 3-30 characters and use only letters, numbers, or underscores."

    try:
        update_username(user_id, new_username)
        return True, "Username updated."
    except sqlite3.IntegrityError:
        return False, "This username is already taken."

def change_password(user_id: int, new_password: str, confirm: str):
    new_password = (new_password or "").strip()
    confirm = (confirm or "").strip()

    if not new_password and not confirm:
        return True, None  # no change

    if not is_valid_password(new_password):
        return False, "Password must be at least 8 characters."

    if new_password != confirm:
        return False, "New passwords do not match."

    update_password_hash(user_id, generate_password_hash(new_password))
    return True, "Password updated."
