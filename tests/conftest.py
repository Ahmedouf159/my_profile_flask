import os
import sys

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app


@pytest.fixture()
def app(tmp_path):
    database = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database),
            "SECRET_KEY": "test-secret",
            "CSRF_ENABLED": False,
            "GOOGLE_CLIENT_ID": "",
            "GOOGLE_CLIENT_SECRET": "",
            "FACEBOOK_CLIENT_ID": "",
            "FACEBOOK_CLIENT_SECRET": "",
        }
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
