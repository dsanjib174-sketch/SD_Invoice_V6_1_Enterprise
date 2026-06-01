from flask import Blueprint, render_template
from .auth import login_required
reports_bp = Blueprint("reports", __name__)
@reports_bp.route("/document-register")
@login_required
def document_register(): return render_template("reports/document_register.html")
@reports_bp.route("/ledger")
@login_required
def ledger(): return render_template("reports/ledger.html")
@reports_bp.route("/gst-gsp")
@login_required
def gst_gsp(): return render_template("reports/gst_gsp.html")
@reports_bp.route("/tally-sap")
@login_required
def tally_sap(): return render_template("reports/tally_sap.html")
