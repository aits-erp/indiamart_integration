import frappe

def process_lead(data):
    try:
        data = frappe._dict(data)

        # 📌 Field Mapping (IndiaMART varies)
        lead_name = data.get("name") or data.get("sender_name") or "Unknown"
        phone = data.get("mobile") or data.get("mobile_no")
        email = data.get("email")
        message = data.get("query") or data.get("message")

        # 🚫 Duplicate Check
        existing = None
        if phone:
            existing = frappe.db.get_value("Lead", {"mobile_no": phone})
        elif email:
            existing = frappe.db.get_value("Lead", {"email_id": email})

        if existing:
            return

        # ✅ Create Lead
        lead = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": lead_name,
            "mobile_no": phone,
            "email_id": email,
            "notes": message,
            "source": "IndiaMART",
            "status": "Open"
        })
        lead.insert(ignore_permissions=True)

        # 👨‍💼 Assign Sales Person
        assign_sales_person(lead)

        # 🧾 Create Customer
        customer = create_customer(lead_name)

        # 💰 Create Opportunity
        create_opportunity(customer)

        # 💬 WhatsApp Auto Reply
        send_whatsapp_reply(phone, lead_name)

        # 📅 Follow-up Task
        create_followup(lead)

        frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "IndiaMART PROCESS ERROR")