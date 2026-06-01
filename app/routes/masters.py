from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .auth import login_required
import os, json, uuid
from datetime import datetime

masters_bp = Blueprint("masters", __name__)
VENDORS_FILE = "vendors.json"
ROC_FILE = "rate_contracts.json"


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


def visible(items):
    if is_superadmin():
        return items
    email = current_user_email()
    return [i for i in items if i.get("client_email") == email or i.get("created_by") == email]


@masters_bp.route("/masters")
@login_required
def masters():
    return render_template("masters/masters.html")


@masters_bp.route("/rate-contract", methods=["GET", "POST"])
@login_required
def rate_contract():
    vendors = load_json(VENDORS_FILE)
    contracts = load_json(ROC_FILE)
    user_email = current_user_email()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "save_vendor":
            vendor_name = request.form.get("vendor_name", "").strip()
            if not vendor_name:
                flash("Vendor name is required.", "error")
                return redirect(url_for("masters.rate_contract"))
            vendors.insert(0, {
                "id": uuid.uuid4().hex,
                "vendor_name": vendor_name,
                "vendor_email": request.form.get("vendor_email", "").strip(),
                "vendor_mobile": request.form.get("vendor_mobile", "").strip(),
                "vendor_gst": request.form.get("vendor_gst", "").strip(),
                "vendor_pan": request.form.get("vendor_pan", "").strip(),
                "vendor_state": request.form.get("vendor_state", "").strip(),
                "vendor_state_code": request.form.get("vendor_state_code", "").strip(),
                "vendor_address": request.form.get("vendor_address", "").strip(),
                "client_email": user_email,
                "created_by": user_email,
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })
            save_json(VENDORS_FILE, vendors)
            flash("Vendor saved successfully.", "success")
        elif action == "save_contract":
            if not request.form.get("vendor_name") or not request.form.get("product_name") or not request.form.get("rate"):
                flash("Vendor, product/service and rate are required.", "error")
                return redirect(url_for("masters.rate_contract"))
            contracts.insert(0, {
                "id": uuid.uuid4().hex,
                "vendor_name": request.form.get("vendor_name", "").strip(),
                "product_name": request.form.get("product_name", "").strip(),
                "hsn_code": request.form.get("hsn_code", "").strip(),
                "unit": request.form.get("unit", "").strip(),
                "rate": request.form.get("rate", "").strip(),
                "gst_percent": request.form.get("gst_percent", "").strip(),
                "valid_from": request.form.get("valid_from", "").strip(),
                "valid_to": request.form.get("valid_to", "").strip(),
                "remarks": request.form.get("remarks", "").strip(),
                "source": "Manual",
                "status": "Active",
                "client_email": user_email,
                "created_by": user_email,
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })
            save_json(ROC_FILE, contracts)
            flash("Rate contract saved successfully.", "success")
        elif action == "update_contract":
            cid = request.form.get("contract_id")
            for c in contracts:
                if c.get("id") == cid:
                    if not is_superadmin() and c.get("client_email") != user_email and c.get("created_by") != user_email:
                        flash("You cannot update another client's contract.", "error")
                        return redirect(url_for("masters.rate_contract"))
                    c.update({
                        "vendor_name": request.form.get("vendor_name", "").strip(),
                        "product_name": request.form.get("product_name", "").strip(),
                        "hsn_code": request.form.get("hsn_code", "").strip(),
                        "unit": request.form.get("unit", "").strip(),
                        "rate": request.form.get("rate", "").strip(),
                        "gst_percent": request.form.get("gst_percent", "").strip(),
                        "valid_from": request.form.get("valid_from", "").strip(),
                        "valid_to": request.form.get("valid_to", "").strip(),
                        "remarks": request.form.get("remarks", "").strip(),
                        "status": request.form.get("status", "Active").strip(),
                        "updated_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    })
                    break
            save_json(ROC_FILE, contracts)
            flash("Rate contract updated successfully.", "success")
        return redirect(url_for("masters.rate_contract"))

    return render_template("masters/rate_contract.html", vendors=visible(vendors), contracts=visible(contracts), is_superadmin=is_superadmin())
