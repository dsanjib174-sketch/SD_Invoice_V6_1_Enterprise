from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .auth import login_required
import os, json, uuid
from datetime import datetime

documents_bp = Blueprint("documents", __name__)
QUOTATION_FILE = "quotations.json"
PROFORMA_FILE = "proformas.json"
INVOICE_FILE = "invoices.json"
DELIVERY_CHALLAN_FILE = "delivery_challans.json"
ROC_FILE = "rate_contracts.json"
VENDORS_FILE = "vendors.json"


def _json_path(filename):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], filename)


def load_json(filename):
    path = _json_path(filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    os.makedirs(os.path.dirname(_json_path(filename)), exist_ok=True)
    with open(_json_path(filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def current_user_email():
    return session.get("user") or session.get("email") or ""


def is_superadmin():
    return session.get("login_type") == "superadmin" or session.get("role") == "superadmin"


def get_financial_year():
    today = datetime.now(); year = today.year
    return f"{str(year)[-2:]}-{str(year + 1)[-2:]}" if today.month >= 4 else f"{str(year - 1)[-2:]}-{str(year)[-2:]}"


def generate_doc_no(prefix, existing_docs):
    return f"SD/{prefix}/{get_financial_year()}/{str(len(existing_docs) + 1).zfill(3)}"


def load_roc(): return load_json(ROC_FILE)
def load_vendors(): return load_json(VENDORS_FILE)


def visible_data(data):
    if is_superadmin():
        return data
    email = current_user_email()
    return [d for d in data if d.get("client_email") == email or d.get("created_by") == email]


def active_contracts():
    data = visible_data(load_roc())
    return [c for c in data if c.get("status", "Active") == "Active"]


def active_vendors():
    names = sorted({c.get("vendor_name", "") for c in active_contracts() if c.get("vendor_name")})
    return names


def save_document(file_name, number_field, number_prefix, status):
    docs = load_json(file_name)
    doc_no = request.form.get(number_field, "").strip() or generate_doc_no(number_prefix, docs)
    item = {
        "id": uuid.uuid4().hex,
        number_field: doc_no,
        "vendor_name": request.form.get("vendor_name", "").strip(),
        "customer_name": request.form.get("customer_name", "").strip(),
        "gstin": request.form.get("gstin", "").strip(),
        "pan": request.form.get("pan", "").strip(),
        "state": request.form.get("state", "").strip(),
        "state_code": request.form.get("state_code", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "billing_address": request.form.get("billing_address", "").strip(),
        "shipping_address": request.form.get("shipping_address", "").strip(),
        "product_name": request.form.get("product_name", "").strip(),
        "description": request.form.get("description", "").strip(),
        "hsn_code": request.form.get("hsn_code", "").strip(),
        "unit": request.form.get("unit", "").strip(),
        "qty": request.form.get("qty", "1").strip(),
        "rate": request.form.get("rate", "0").strip(),
        "discount": request.form.get("discount", "0").strip(),
        "gst_percent": request.form.get("gst_percent", "0").strip(),
        "taxable_amount": request.form.get("taxable_amount", "0").strip(),
        "cgst": request.form.get("cgst", "0").strip(),
        "sgst": request.form.get("sgst", "0").strip(),
        "igst": request.form.get("igst", "0").strip(),
        "total_gst": request.form.get("total_gst", "0").strip(),
        "grand_total": request.form.get("grand_total", "0").strip(),
        "remarks": request.form.get("remarks", "").strip(),
        "status": status,
        "client_email": current_user_email(),
        "created_by": current_user_email(),
        "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
    }
    docs.insert(0, item)
    save_json(file_name, docs)
    return item


def common_context(file_name, prefix):
    docs = load_json(file_name)
    return {
        "vendors": active_vendors(),
        "contracts": active_contracts(),
        "vendor_records": visible_data(load_vendors()),
        "doc_no": generate_doc_no(prefix, docs)
    }


@documents_bp.route("/quotation", methods=["GET", "POST"])
@login_required
def quotation():
    quotations = load_json(QUOTATION_FILE)
    contracts = load_roc()
    user_email = current_user_email()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save_quotation":
            save_document(QUOTATION_FILE, "quotation_no", "QT", "Pending")
            flash("Quotation saved successfully.", "success")
        elif action == "update_quotation":
            qid = request.form.get("quotation_id")
            for q in quotations:
                if q.get("id") == qid:
                    if q.get("status") == "Approved":
                        flash("Approved quotation cannot be edited.", "error"); return redirect(url_for("documents.quotation"))
                    q.update({"quotation_no": request.form.get("quotation_no", "").strip(), "vendor_name": request.form.get("vendor_name", "").strip(), "customer_name": request.form.get("customer_name", "").strip(), "product_name": request.form.get("product_name", "").strip(), "hsn_code": request.form.get("hsn_code", "").strip(), "unit": request.form.get("unit", "").strip(), "qty": request.form.get("qty", "1").strip(), "rate": request.form.get("rate", "0").strip(), "gst_percent": request.form.get("gst_percent", "0").strip(), "taxable_amount": request.form.get("taxable_amount", "0").strip(), "cgst": request.form.get("cgst", "0").strip(), "sgst": request.form.get("sgst", "0").strip(), "igst": request.form.get("igst", "0").strip(), "total_gst": request.form.get("total_gst", "0").strip(), "grand_total": request.form.get("grand_total", "0").strip(), "remarks": request.form.get("remarks", "").strip(), "updated_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")}); break
            save_json(QUOTATION_FILE, quotations); flash("Quotation updated successfully.", "success")
        elif action == "approve_quotation":
            qid = request.form.get("quotation_id")
            for q in quotations:
                if q.get("id") == qid:
                    if q.get("status") == "Approved": flash("Quotation already approved.", "error"); return redirect(url_for("documents.quotation"))
                    q["status"] = "Approved"; q["approved_by"] = user_email; q["approved_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    contracts.insert(0, {"id": uuid.uuid4().hex, "vendor_name": q.get("vendor_name", ""), "product_name": q.get("product_name", ""), "hsn_code": q.get("hsn_code", ""), "unit": q.get("unit", ""), "rate": q.get("rate", ""), "gst_percent": q.get("gst_percent", ""), "valid_from": datetime.now().strftime("%Y-%m-%d"), "valid_to": "", "remarks": "Auto created from approved quotation " + q.get("quotation_no", ""), "source": "Approved Quotation", "status": "Active", "client_email": q.get("client_email", user_email), "created_by": user_email, "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")}); break
            save_json(QUOTATION_FILE, quotations); save_json(ROC_FILE, contracts); flash("Quotation approved and rate added to ROC successfully.", "success")
        return redirect(url_for("documents.quotation"))
    ctx = common_context(QUOTATION_FILE, "QT"); ctx["quotations"] = visible_data(quotations)
    return render_template("documents/quotation.html", **ctx)


@documents_bp.route("/proforma", methods=["GET", "POST"])
@login_required
def proforma():
    proformas = load_json(PROFORMA_FILE)
    if request.method == "POST":
        save_document(PROFORMA_FILE, "proforma_no", "PI", "Pending")
        flash("Proforma invoice saved successfully.", "success")
        return redirect(url_for("documents.proforma"))
    ctx = common_context(PROFORMA_FILE, "PI"); ctx["proformas"] = visible_data(proformas)
    return render_template("documents/proforma.html", **ctx)


@documents_bp.route("/invoice", methods=["GET", "POST"])
@login_required
def invoice():
    invoices = load_json(INVOICE_FILE)
    if request.method == "POST":
        save_document(INVOICE_FILE, "invoice_no", "INV", "Generated")
        flash("Tax invoice saved successfully.", "success")
        return redirect(url_for("documents.invoice"))
    ctx = common_context(INVOICE_FILE, "INV"); ctx["invoices"] = visible_data(invoices)
    return render_template("documents/invoice.html", **ctx)


@documents_bp.route("/invoice/preview")
@login_required
def invoice_preview():
    return render_template("invoice/professional_invoice.html")


@documents_bp.route("/delivery-challan", methods=["GET", "POST"])
@login_required
def delivery_challan():
    challans = load_json(DELIVERY_CHALLAN_FILE)
    if request.method == "POST":
        save_document(DELIVERY_CHALLAN_FILE, "challan_no", "DC", "Generated")
        flash("Delivery challan saved successfully.", "success")
        return redirect(url_for("documents.delivery_challan"))
    ctx = common_context(DELIVERY_CHALLAN_FILE, "DC"); ctx["challans"] = visible_data(challans)
    return render_template("documents/delivery_challan.html", **ctx)


@documents_bp.route("/receipts")
@login_required
def receipts(): return render_template("documents/receipts.html")


@documents_bp.route("/credit-note")
@login_required
def credit_note(): return render_template("documents/credit_note.html")
