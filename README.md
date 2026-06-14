# Codac with Ahmed Flask Portfolio

A polished personal portfolio and account system for Codac with Ahmed, built with Flask, SQLite, Jinja templates, and vanilla CSS/JavaScript.

## Features

- App factory with blueprints for pages, auth, user, and settings routes
- SQLite user storage with a small schema migration for the saved theme field
- Signup, login, logout, dashboard, profile, password update, and protected settings page
- Optional Google and Facebook login through OAuth
- Hashed passwords with Werkzeug
- CSRF protection for mutating requests
- Safer session cookie settings
- Responsive portfolio UI with project case studies, contact flows, and dark/light/system theme
- Pytest coverage for pages, auth, profile, CSRF, and theme behavior
- GitHub Actions workflow for automated test runs

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

Local secrets are loaded from `.env`. Add Google/Facebook client secrets there once, then you only need to run `python app.py` or Waitress.

## Tests

```powershell
python -m pytest
```

The same command runs in CI through `.github/workflows/tests.yml`.

## Social Login

Install dependencies, then create OAuth apps with these local callback URLs:

```text
http://127.0.0.1:5000/auth/google/callback
http://127.0.0.1:5000/auth/facebook/callback
```

Set the credentials before running Flask:

```powershell
$env:GOOGLE_CLIENT_ID = "your-google-client-id"
$env:GOOGLE_CLIENT_SECRET = "your-google-client-secret"
$env:FACEBOOK_CLIENT_ID = "your-facebook-client-id"
$env:FACEBOOK_CLIENT_SECRET = "your-facebook-client-secret"
```

## Production Notes

Set a real secret key before deployment:
Set `FLASK_CONTACT_EMAIL` to Ahmed's real email so all contact buttons open an active email draft.

```powershell
$env:FLASK_SECRET_KEY = "a-long-random-secret"
$env:FLASK_ENVIRONMENT = "production"
$env:FLASK_CONTACT_EMAIL = "ah0349900@gmail.com"
$env:FLASK_SITE_URL = "https://your-domain.com"
$env:FLASK_GITHUB_URL = "https://github.com/Ahmedouf159"
```

On Windows, Waitress is a simple WSGI server option:

```powershell
waitress-serve --listen=0.0.0.0:5000 app:app
```

Do not use Flask's built-in development server for public production traffic.
