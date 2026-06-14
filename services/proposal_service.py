from __future__ import annotations

import textwrap
from urllib.parse import quote as url_quote

from services.project_ml_service import BUDGETS, DEADLINES, FEATURES, PROJECT_TYPES, predict_project_success


PROJECT_LABELS = {
    "portfolio": "Portfolio website",
    "business": "Business website",
    "store": "Store website",
    "dashboard": "Dashboard app",
}

FEATURE_LABELS = {
    "contact": "Contact form and social buttons",
    "auth": "Login and signup system",
    "socialAuth": "Google or Facebook login",
    "admin": "Admin dashboard",
    "database": "Database setup",
    "payments": "Payment page setup",
}


def proposal_payload_from_args(args) -> dict:
    project_type = args.get("projectType", "portfolio")
    deadline = args.get("deadline", "normal")
    budget = args.get("budget", "medium")

    if project_type not in PROJECT_TYPES:
        project_type = "portfolio"
    if deadline not in DEADLINES:
        deadline = "normal"
    if budget not in BUDGETS:
        budget = "medium"

    try:
        pages = int(args.get("pages", 3))
    except (TypeError, ValueError):
        pages = 3

    selected_features = [feature for feature in args.getlist("features") if feature in FEATURES]

    return {
        "projectType": project_type,
        "pages": max(1, min(pages, 12)),
        "deadline": deadline,
        "budget": budget,
        "features": selected_features,
    }


def _expanded_features(payload: dict) -> set[str]:
    features = set(payload.get("features") or [])
    if "socialAuth" in features:
        features.add("auth")
    if payload.get("projectType") in {"store", "dashboard"}:
        features.add("database")
    return features


def _roadmap(payload: dict, prediction) -> list[dict]:
    project_type = payload["projectType"]
    pages = payload["pages"]
    features = _expanded_features(payload)
    target_days = max(int(prediction.days_max), 5)

    phases = [
        {
            "title": "Discovery",
            "detail": f"Confirm {PROJECT_LABELS[project_type]} goals, pages, content, and success target.",
            "weight": 1,
        },
        {
            "title": "UI Design",
            "detail": "Design main screens, mobile layout, buttons, and visual style.",
            "weight": 2 if pages >= 5 else 1,
        },
        {
            "title": "Frontend Build",
            "detail": "Build responsive pages, forms, interactions, and polished states.",
            "weight": max(1, (pages + 2) // 3),
        },
    ]

    optional_phases = [
        ("auth", "Account System", "Add signup, login, logout, sessions, validation, and protected pages."),
        ("socialAuth", "OAuth Setup", "Connect Google/Facebook login, callbacks, and provider settings."),
        ("database", "Data Layer", "Create database tables, saved actions, and admin-ready data."),
        ("admin", "Admin Panel", "Add owner-only stats, recent activity, controls, and clean dashboards."),
        ("payments", "Payment Flow", "Prepare checkout screens, order states, and payment safety checks."),
    ]

    for feature, title, detail in optional_phases:
        if feature in features:
            phases.append({"title": title, "detail": detail, "weight": 2})

    phases.extend(
        [
            {
                "title": "Testing",
                "detail": "Test forms, login, mobile screens, links, and main user paths.",
                "weight": 1 if payload["deadline"] == "urgent" else 2,
            },
            {
                "title": "Launch",
                "detail": "Deploy, check live URLs, prepare handoff notes, and confirm analytics.",
                "weight": 1,
            },
        ]
    )

    total_weight = sum(phase["weight"] for phase in phases)
    used_days = 0
    roadmap = []

    for index, phase in enumerate(phases):
        remaining_phases = len(phases) - index
        remaining_days = max(remaining_phases, target_days - used_days)
        max_for_phase = max(1, remaining_days - (remaining_phases - 1))
        suggested_days = max(1, round((phase["weight"] / total_weight) * target_days))
        duration = remaining_days if index == len(phases) - 1 else min(max_for_phase, suggested_days)
        start = used_days + 1
        used_days += duration
        end = used_days
        roadmap.append(
            {
                "range": f"Day {start}" if start == end else f"Days {start}-{end}",
                "title": phase["title"],
                "detail": phase["detail"],
            }
        )

    return roadmap


def _checklist(payload: dict) -> list[str]:
    features = _expanded_features(payload)
    items = [
        "Final text, images, links, and brand name are ready.",
        "Test the full website on phone, tablet, and desktop.",
        "Check every contact, GitHub, YouTube, and email link.",
    ]

    if "auth" in features:
        items.append("Create a real test account and check logout/session behavior.")
    if "socialAuth" in features:
        items.append("Add the final public OAuth redirect URLs before deployment.")
    if features.intersection({"database", "admin"}):
        items.append("Create the owner admin account and test saved data.")
    if "payments" in features:
        items.append("Use sandbox payments first, then enable live keys only after testing.")
    if payload["deadline"] == "urgent":
        items.append("Freeze new features before launch so testing stays clean.")

    return items[:7]


def _wrap_lines(lines: list[str], width: int = 88) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(textwrap.wrap(line, width=width, break_long_words=False) or [""])
    return wrapped


def _pdf_escape(value: str) -> str:
    clean = str(value).encode("latin-1", "replace").decode("latin-1")
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_pdf(lines: list[str]) -> bytes:
    page_width = 612
    page_height = 792
    margin_x = 54
    line_height = 15
    top_y = 738
    bottom_y = 54
    lines_per_page = max(1, (top_y - bottom_y) // line_height)
    pages = [lines[index : index + lines_per_page] for index in range(0, len(lines), lines_per_page)]

    page_count = max(1, len(pages))
    font_id = 1
    pages_id = 2 + page_count * 2
    catalog_id = pages_id + 1
    objects: dict[int, bytes] = {
        font_id: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    page_ids = []

    for index, page_lines in enumerate(pages):
        content_id = 2 + index * 2
        page_id = content_id + 1
        page_ids.append(page_id)

        stream_lines = [
            "BT",
            "/F1 10 Tf",
            f"{line_height} TL",
            f"{margin_x} {top_y} Td",
        ]
        for line in page_lines:
            stream_lines.append(f"({_pdf_escape(line)}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1")
        objects[content_id] = (
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        objects[page_id] = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    objects[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for object_id in range(1, catalog_id + 1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode("ascii"))
        output.extend(objects[object_id])
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {catalog_id + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {catalog_id + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(output)


def build_proposal_pdf(payload: dict, brand_name: str, contact_email: str) -> bytes:
    prediction = predict_project_success(payload)
    roadmap = _roadmap(payload, prediction)
    checklist = _checklist(payload)
    selected_features = payload.get("features") or []
    feature_names = [FEATURE_LABELS[feature] for feature in selected_features if feature in FEATURE_LABELS]

    lines = [
        f"{brand_name} - Project Proposal",
        "=" * 72,
        "",
        "Project Summary",
        f"Project type: {PROJECT_LABELS[payload['projectType']]}",
        f"Pages: {payload['pages']}",
        f"Deadline: {payload['deadline'].title()}",
        f"Budget: {payload['budget'].title()}",
        f"Features: {', '.join(feature_names) if feature_names else 'No extra features selected'}",
        "",
        "ML Estimate",
        f"Package: {prediction.package}",
        f"Estimated price: ${prediction.price_min} - ${prediction.price_max}",
        f"Estimated time: {prediction.days_min} - {prediction.days_max} days",
        f"Success score: {prediction.success_score}/100",
        f"Risk: {prediction.risk}",
        f"Model engine: {prediction.model_engine}",
        "",
        "ML Advice",
        *[f"- {item}" for item in prediction.advice],
        "",
        "Build Roadmap",
        *[f"- {phase['range']}: {phase['title']} - {phase['detail']}" for phase in roadmap],
        "",
        "Launch Checklist",
        *[f"- {item}" for item in checklist],
        "",
        "Next Step",
        f"Email {contact_email} to confirm the final scope, real content, and launch date.",
        "",
        "Generated by the Codac with Ahmed quote builder.",
    ]

    return _simple_pdf(_wrap_lines(lines))


def proposal_filename(payload: dict) -> str:
    project_type = url_quote(PROJECT_LABELS.get(payload.get("projectType"), "project-proposal").lower().replace(" ", "-"))
    return f"codac-{project_type}-proposal.pdf"
