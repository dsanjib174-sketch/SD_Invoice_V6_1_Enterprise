from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from .auth import login_required
import os, json, uuid
from datetime import datetime

masters_bp = Blueprint("masters", __name__)

VENDORS_FILE = "vendors.json"
CUSTOMERS_FILE = "customers.json"
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


def load_vendors():
    return load_json(VENDORS_FILE)


def load_customers():
    return load_json(CUSTOMERS_FILE)


@masters_bp.route("/masters")
@login_required
def masters_home():
    return render_template("masters/index.html")


@masters_bp.route("/customer-master", methods=["GET", "POST"])
@login_required
def customer_master():
    customers = load_customers()
    user_email = current_user_email()

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        gst_number = request.form.get("gst_number", "").strip()
        pan_number = request.form.get("pan_number", "").strip()
        customer_address = request.form.get("customer_address", "").strip()

        if not company_name:
            flash("Company name is required.", "error")
            return redirect(url_for("masters.customer_master"))

        customers.insert(0, {
            "id": uuid.uuid4().hex,
            "company_name": company_name,
            "gst_number": gst_number,
            "pan_number": pan_number,
            "customer_address": customer_address,
            "client_email": user_email,
            "created_by": user_email,
            "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })

        save_json(CUSTOMERS_FILE, customers)
        flash("Customer saved successfully.", "success")
        return redirect(url_for("masters.customer_master"))

    if not is_superadmin():
        customers = [c for c in customers if c.get("client_email") == user_email]

    return render_template("masters/customer_master.html", customers=customers)


@masters_bp.route("/rate-contract", methods=["GET", "POST"])
@login_required
def rate_contract():
    vendors = load_vendors()
    customers = load_customers()
    contracts = load_json(ROC_FILE)
    user_email = current_user_email()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "save_vendor":
            vendors.insert(0, {
                "id": uuid.uuid4().hex,
                "vendor_name": request.form.get("vendor_name", "").strip(),
                "vendor_email": request.form.get("vendor_email", "").strip(),
                "vendor_mobile": request.form.get("vendor_mobile", "").strip(),
                "vendor_gst": request.form.get("vendor_gst", "").strip(),
                "vendor_pan": request.form.get("vendor_pan", "").strip(),
                "vendor_address": request.form.get("vendor_address", "").strip(),
                "client_email": user_email,
                "created_by": user_email,
                "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })

            save_json(VENDORS_FILE, vendors)
            flash("Vendor saved successfully.", "success")

        elif action == "save_contract":
            contracts.insert(0, {
                "id": uuid.uuid4().hex,

                "customer_name": request.form.get("customer_name", "").strip(),
                "customer_gst": request.form.get("customer_gst", "").strip(),
                "customer_pan": request.form.get("customer_pan", "").strip(),
                "customer_address": request.form.get("customer_address", "").strip(),

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
            contract_id = request.form.get("contract_id")

            for c in contracts:
                if c.get("id") == contract_id:
                    if not is_superadmin() and c.get("client_email") != user_email:
                        flash("You cannot update another client's contract.", "error")
                        return redirect(url_for("masters.rate_contract"))

                    c["customer_name"] = request.form.get("customer_name", "").strip()
                    c["customer_gst"] = request.form.get("customer_gst", "").strip()
                    c["customer_pan"] = request.form.get("customer_pan", "").strip()
                    c["customer_address"] = request.form.get("customer_address", "").strip()

                    c["vendor_name"] = request.form.get("vendor_name", "").strip()
                    c["product_name"] = request.form.get("product_name", "").strip()
                    c["hsn_code"] = request.form.get("hsn_code", "").strip()
                    c["unit"] = request.form.get("unit", "").strip()
                    c["rate"] = request.form.get("rate", "").strip()
                    c["gst_percent"] = request.form.get("gst_percent", "").strip()
                    c["valid_from"] = request.form.get("valid_from", "").strip()
                    c["valid_to"] = request.form.get("valid_to", "").strip()
                    c["remarks"] = request.form.get("remarks", "").strip()
                    c["status"] = request.form.get("status", "Active")
                    c["updated_at"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    break

            save_json(ROC_FILE, contracts)
            flash("Rate contract updated successfully.", "success")

        return redirect(url_for("masters.rate_contract"))

    if not is_superadmin():
        vendors = [v for v in vendors if v.get("client_email") == user_email]
        customers = [c for c in customers if c.get("client_email") == user_email]
        contracts = [c for c in contracts if c.get("client_email") == user_email]

    return render_template(
        "masters/rate_contract.html",
        vendors=vendors,
        customers=customers,
        contracts=contracts
    )
