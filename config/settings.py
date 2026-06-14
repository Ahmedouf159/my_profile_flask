import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE = os.path.join(INSTANCE_DIR, "app.db")

ENVIRONMENT = os.environ.get("FLASK_ENVIRONMENT", "development")
DEV_SECRET_KEY = "dev-only-change-me"
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

PERMANENT_SESSION_LIFETIME = timedelta(days=14)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = ENVIRONMENT == "production"
CSRF_ENABLED = True
MAX_CONTENT_LENGTH = 2 * 1024 * 1024
CONTACT_EMAIL = os.environ.get("FLASK_CONTACT_EMAIL", "ah0349900@gmail.com")
BRAND_NAME = os.environ.get("FLASK_BRAND_NAME", "Codac with Ahmed")
YOUTUBE_HANDLE = os.environ.get("FLASK_YOUTUBE_HANDLE", "@A7med-code")
YOUTUBE_URL = os.environ.get("FLASK_YOUTUBE_URL", "https://www.youtube.com/channel/UCT0xlDQpWRaoBcnQccRV7HA")
GITHUB_URL = os.environ.get("FLASK_GITHUB_URL", "https://github.com/Ahmedouf159")
SITE_URL = os.environ.get("FLASK_SITE_URL", "http://127.0.0.1:5000").rstrip("/")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
FACEBOOK_CLIENT_ID = os.environ.get("FACEBOOK_CLIENT_ID", "").strip()
FACEBOOK_CLIENT_SECRET = os.environ.get("FACEBOOK_CLIENT_SECRET", "").strip()

SECRET_OFFER_CODE = os.environ.get("SECRET_OFFER_CODE", "CODAC10").strip().upper()
SECRET_OFFER_NAME = os.environ.get("SECRET_OFFER_NAME", "Starter Website Package")
SECRET_OFFER_PRICE = os.environ.get("SECRET_OFFER_PRICE", "$25")
