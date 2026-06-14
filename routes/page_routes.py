from flask import Blueprint, Response, current_app, render_template, request

from services.proposal_service import build_proposal_pdf, proposal_filename, proposal_payload_from_args

page_bp = Blueprint("pages", __name__)

@page_bp.get("/")
def index():
    return render_template("index.html")

@page_bp.get("/about")
def about():
    return render_template("about.html")

@page_bp.get("/services")
def services():
    return render_template("services.html")

@page_bp.get("/quote")
def quote():
    return render_template("quote.html")

@page_bp.get("/quote/proposal.pdf")
def quote_proposal_pdf():
    payload = proposal_payload_from_args(request.args)
    pdf = build_proposal_pdf(
        payload,
        brand_name=current_app.config["BRAND_NAME"],
        contact_email=current_app.config["CONTACT_EMAIL"],
    )
    filename = proposal_filename(payload)
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@page_bp.get("/projects")
def projects():
    return render_template("projects.html")

@page_bp.get("/blank")
def blank():
    return render_template("blank.html")
