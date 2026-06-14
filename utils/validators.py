import re

def is_valid_email(email: str) -> bool:
    email = (email or "").strip().lower()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def is_valid_username(username: str) -> bool:
    username = (username or "").strip()
    return bool(re.match(r"^[A-Za-z0-9_]{3,30}$", username))

def is_valid_password(password: str) -> bool:
    password = password or ""
    return len(password) >= 8
