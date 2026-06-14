import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from utils.validators import is_valid_email, is_valid_username, is_valid_password
from models.user_model import create_user, find_user_by_login

def signup_user(username: str, email: str, password: str, confirm: str):
    username = (username or "").strip()
    email = (email or "").strip().lower()

    if not username or not email or not password or not confirm:
        return False, "Please fill all fields."

    if not is_valid_username(username):
        return False, "Username must be 3-30 characters and use only letters, numbers, or underscores."

    if not is_valid_email(email):
        return False, "Please enter a valid email."

    if not is_valid_password(password):
        return False, "Password must be at least 8 characters."

    if password != confirm:
        return False, "Passwords do not match."

    try:
        create_user(username, email, generate_password_hash(password))
        return True, "Account created. Please login."
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."

def login_user(login_id: str, password: str):
    user = find_user_by_login(login_id)
    if not user:
        return None, "Invalid username/email or password."

    if not check_password_hash(user["password_hash"], password or ""):
        return None, "Invalid username/email or password."

    return user, "Welcome back!"
