from app import create_app


def signup(client, username="ahmed", email="ahmed@example.com", password="password123"):
    return client.post(
        "/signup",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def login(client, identity="ahmed", password="password123"):
    return client.post(
        "/login",
        data={"identity": identity, "password": password},
        follow_redirects=True,
    )


def test_public_pages_load(client):
    for path in ["/", "/about", "/services", "/pricing", "/quote", "/projects", "/testimonials", "/case-studies"]:
        response = client.get(path)
        assert response.status_code == 200


def test_homepage_showcases_portfolio_content(client):
    response = client.get("/")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="description"' in text
    assert 'property="og:title"' in text
    assert 'rel="canonical"' in text
    assert "Codac with Ahmed" in text
    assert "@A7med-code" in text
    assert "Ahmed builds Flask apps that feel complete" in text
    assert "Featured Work" in text
    assert "Portfolio Auth System" in text
    assert "https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=ah0349900%40gmail.com" in text
    assert "https://github.com/Ahmedouf159" in text
    assert "https://www.youtube.com/channel/UCT0xlDQpWRaoBcnQccRV7HA" in text


def test_security_headers_are_present(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_health_robots_and_sitemap(client):
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json() == {"ok": True, "service": "Codac with Ahmed"}

    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap: http://127.0.0.1:5000/sitemap.xml" in robots.get_data(as_text=True)

    sitemap = client.get("/sitemap.xml")
    text = sitemap.get_data(as_text=True)
    assert sitemap.status_code == 200
    assert "<urlset" in text
    assert "http://127.0.0.1:5000/quote" in text
    assert "http://127.0.0.1:5000/projects" in text


def test_contact_email_can_be_configured(app):
    app.config["CONTACT_EMAIL"] = "hello@ahmed.dev"
    client = app.test_client()

    response = client.get("/")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=hello%40ahmed.dev" in text


def test_projects_page_reads_like_case_studies(client):
    response = client.get("/projects")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Selected Projects" in text
    assert "Search & Filter UI" in text
    assert "Role" in text
    assert "Impact" in text
    assert "https://github.com/Ahmedouf159" in text
    assert "https://www.youtube.com/channel/UCT0xlDQpWRaoBcnQccRV7HA" in text


def test_case_study_detail_page_loads(client):
    response = client.get("/case-studies/smart-quote-builder")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Smart Quote Builder" in text
    assert "Challenge" in text
    assert "Solution" in text


def test_quote_builder_page_renders(client):
    response = client.get("/quote")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Project Quote Builder" in text
    assert "Email Ahmed This Quote" in text
    assert "Save To Client Portal" in text
    assert "Download Proposal PDF" in text
    assert "ML Success Prediction" in text
    assert "Build Roadmap" in text
    assert "roadmapTimeline" in text
    assert "quoteForm" in text
    assert "portfolio" in text


def test_quote_proposal_pdf_downloads(client):
    response = client.get(
        "/quote/proposal.pdf?projectType=dashboard&pages=5&deadline=fast&budget=medium"
        "&features=auth&features=admin"
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert "attachment;" in response.headers["Content-Disposition"]
    assert "codac-dashboard-app-proposal.pdf" in response.headers["Content-Disposition"]


def test_project_prediction_api_returns_ml_result(client):
    response = client.post(
        "/api/project-prediction",
        json={
            "projectType": "dashboard",
            "pages": 5,
            "deadline": "fast",
            "budget": "medium",
            "features": ["auth", "admin", "database"],
        },
    )
    data = response.get_json()
    prediction = data["prediction"]

    assert response.status_code == 200
    assert data["ok"] is True
    assert prediction["package"] in {"Starter", "Pro", "Advanced"}
    assert 25 <= prediction["success_score"] <= 96
    assert prediction["risk"] in {"Low", "Medium", "High"}
    assert prediction["price_min"] < prediction["price_max"]
    assert prediction["days_min"] < prediction["days_max"]
    assert prediction["model_engine"] in {"NumPy linear regression", "scikit-learn Ridge"}
    assert prediction["advice"]


def test_logged_in_user_can_save_quote_to_client_portal(client):
    signup(client)
    login(client)

    prediction_response = client.post(
        "/api/project-prediction",
        json={
            "projectType": "dashboard",
            "pages": 5,
            "deadline": "normal",
            "budget": "high",
            "features": ["auth", "admin", "database"],
        },
    )
    prediction_id = prediction_response.get_json()["prediction_id"]

    save_response = client.post("/api/quotes/save", json={"prediction_id": prediction_id})
    assert save_response.status_code == 200
    assert save_response.get_json() == {"ok": True, "message": "Quote saved to your client portal."}

    dashboard = client.get("/dashboard")
    text = dashboard.get_data(as_text=True)
    assert "Saved Quotes" in text
    assert "Project Tracker" in text
    assert "Quote saved to your portal" in text
    assert "Dashboard" in text


def test_project_room_messages_files_and_approval(client):
    signup(client)
    login(client)

    prediction_response = client.post(
        "/api/project-prediction",
        json={
            "projectType": "business",
            "pages": 3,
            "deadline": "normal",
            "budget": "medium",
            "features": ["contact", "database"],
        },
    )
    prediction_id = prediction_response.get_json()["prediction_id"]
    client.post("/api/quotes/save", json={"prediction_id": prediction_id})

    dashboard = client.get("/dashboard")
    text = dashboard.get_data(as_text=True)
    assert "Open Project Room" in text

    room = client.get("/dashboard/projects/1")
    assert room.status_code == 200
    assert "Milestones" in room.get_data(as_text=True)

    client.post("/dashboard/projects/1/message", data={"body": "I need a booking section."})
    client.post(
        "/dashboard/projects/1/file",
        data={"label": "Brand logo", "file_url": "https://example.com/logo.png"},
    )
    client.post("/dashboard/projects/1/approve", follow_redirects=True)

    room = client.get("/dashboard/projects/1")
    text = room.get_data(as_text=True)
    assert "I need a booking section." in text
    assert "Brand logo" in text
    assert "Proposal Approved" in text


def test_admin_panel_requires_login(client):
    response = client.get("/admin", follow_redirects=True)
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please login first" in text
    assert "Login" in text


def test_admin_panel_shows_ml_charts_and_recent_predictions(client):
    signup(client)
    login(client)

    client.post(
        "/api/project-prediction",
        json={
            "projectType": "store",
            "pages": 5,
            "deadline": "normal",
            "budget": "high",
            "features": ["contact", "database", "payments"],
        },
    )

    response = client.get("/admin")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Admin Panel" in text
    assert "Lead CRM" in text
    assert "Project Types" in text
    assert "Risk Levels" in text
    assert "Recent ML Predictions" in text
    assert "store" in text


def test_non_admin_cannot_open_admin_panel(client):
    signup(client, username="owner", email="owner@example.com")
    client.get("/logout")
    signup(client, username="visitor", email="visitor@example.com")
    login(client, identity="visitor")

    response = client.get("/admin", follow_redirects=True)
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Admin access only" in text
    assert "Dashboard" in text


def test_signup_form_renders_csrf_field(client):
    response = client.get("/signup")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="_csrf_token"' in text


def test_social_auth_buttons_render_with_setup_state(client):
    response = client.get("/login")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/auth/google" in text
    assert "/auth/facebook" in text
    assert "Google" in text
    assert "Facebook" in text
    assert "Install Authlib" in text or "Add the Google OAuth client ID and secret" in text


def test_unconfigured_social_login_redirects_to_login(client):
    response = client.get("/auth/google", follow_redirects=True)
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Google login is not configured yet" in text
    assert "Welcome back" in text


def test_malformed_google_oauth_config_is_not_enabled(tmp_path):
    database = tmp_path / "oauth.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database),
            "SECRET_KEY": "test-secret",
            "CSRF_ENABLED": False,
            "GOOGLE_CLIENT_ID": "not-a-google-client-id",
            "GOOGLE_CLIENT_SECRET": "not-a-google-secret",
            "FACEBOOK_CLIENT_ID": "",
            "FACEBOOK_CLIENT_SECRET": "",
        }
    )

    client = app.test_client()
    response = client.get("/login")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'aria-disabled="true"' in text
    assert "Google OAuth client ID format looks wrong." in text


def test_signup_login_logout_flow(client):
    response = signup(client)
    assert response.status_code == 200
    assert "Account created" in response.get_data(as_text=True)

    response = login(client)
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Dashboard" in text
    assert "Welcome back" in text

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert "Logged out successfully" in response.get_data(as_text=True)


def test_duplicate_signup_fails(client):
    signup(client)
    response = signup(client)
    assert "Username or email already exists" in response.get_data(as_text=True)


def test_invalid_signup_validation(client):
    response = signup(client, username="ab", email="not-an-email")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Username must be 3-30 characters" in text


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Please login first" in text
    assert "Login" in text


def test_profile_update(client):
    signup(client)
    login(client)

    response = client.post(
        "/profile",
        data={"username": "ahmed_new", "new_password": "", "confirm_new_password": ""},
        follow_redirects=True,
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Username updated" in text
    assert "ahmed_new" in text


def test_theme_api_updates_preference(client):
    signup(client)
    login(client)

    response = client.post("/api/theme", json={"theme": "dark"})

    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "theme": "dark"}


def test_theme_api_rejects_invalid_value(client):
    signup(client)
    login(client)

    response = client.post("/api/theme", json={"theme": "neon"})

    assert response.status_code == 400
    assert response.get_json() == {"ok": False, "error": "Invalid theme."}


def test_secret_offer_reveals_package_for_valid_code(client):
    signup(client)
    login(client)

    response = client.post("/api/secret-offer", json={"code": "codac10"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["offer"]["name"] == "Starter Website Package"
    assert data["offer"]["price"] == "$25"
    assert "3 page responsive website" in data["offer"]["includes"]


def test_secret_offer_rejects_invalid_code(client):
    signup(client)
    login(client)

    response = client.post("/api/secret-offer", json={"code": "wrong"})

    assert response.status_code == 400
    assert response.get_json() == {"ok": False, "error": "Invalid secret code."}


def test_first_time_user_dashboard_shows_onboarding(client):
    signup(client)
    login(client)

    response = client.get("/dashboard")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="onboardingTour"' in text
    assert 'data-onboarding="pending"' in text
    assert "First time setup" in text


def test_user_can_complete_onboarding(client):
    signup(client)
    login(client)

    response = client.post("/api/onboarding/complete", json={})
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    response = client.get("/dashboard")
    text = response.get_data(as_text=True)
    assert 'id="onboardingTour"' not in text
    assert 'data-onboarding="done"' in text


def test_csrf_blocks_missing_token(tmp_path):
    database = tmp_path / "csrf.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database),
            "SECRET_KEY": "test-secret",
            "CSRF_ENABLED": True,
        }
    )

    client = app.test_client()
    response = client.post(
        "/signup",
        data={
            "username": "csrf_user",
            "email": "csrf@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 302
