import frappe

def process_lead(data):
    """
    Process lead from IndiaMART webhook payload.
    Expects data dict with keys like SENDER_NAME, SENDER_MOBILE, etc.
    """
    try:
        if not isinstance(data, dict):
            data = frappe._dict(data)

        # ----- Extract all IndiaMART fields -----
        lead_name = data.get("SENDER_NAME") or "Unknown"
        company = data.get("SENDER_COMPANY")
        mobile = data.get("SENDER_MOBILE") or data.get("mobile") or data.get("mobile_no")
        email = data.get("SENDER_EMAIL") or data.get("email")
        landline = data.get("SENDER_PHONE")
        address = data.get("SENDER_ADDRESS")
        city = data.get("SENDER_CITY")
        state = data.get("SENDER_STATE")
        pincode = data.get("SENDER_PINCODE")
        country_iso = data.get("SENDER_COUNTRY_ISO") or "IN"
        subject = data.get("SUBJECT")
        query_message = data.get("QUERY_MESSAGE")
        query_time = data.get("QUERY_TIME")
        query_type = data.get("QUERY_TYPE")
        product_name = data.get("QUERY_PRODUCT_NAME") or data.get("QUERY_MCAT_NAME")
        unique_query_id = data.get("UNIQUE_QUERY_ID")
        call_duration = data.get("CALL_DURATION")

        # Normalize mobile (remove +91, spaces, dashes)
        if mobile:
            mobile = mobile.replace("+91", "").replace("-", "").replace(" ", "").strip()
        if landline:
            landline = landline.replace("-", "").replace(" ", "").strip()

        # Combine subject + message for notes
        notes = f"Subject: {subject}\n\n{query_message}" if subject else query_message

        # ----- Duplicate Check (by mobile, email, or unique query ID) -----
        duplicate = False
        if mobile:
            duplicate = frappe.db.exists("Lead", {"mobile_no": mobile})
        if not duplicate and email:
            duplicate = frappe.db.exists("Lead", {"email_id": email})
        if not duplicate and unique_query_id:
            # Use a custom field to store unique_query_id
            duplicate = frappe.db.exists("Lead", {"custom_unique_query_id": unique_query_id})

        if duplicate:
            frappe.logger().info(f"Duplicate IndiaMART lead ignored: {mobile} / {unique_query_id}")
            return

        # ----- Create Lead -----
        lead = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": lead_name,
            "company_name": company,
            "mobile_no": mobile,
            "email_id": email,
            "phone": landline,                     # Store landline in phone field
            "address": address,
            "city": city,                          # Requires custom field or use territory
            "state": state,                        # Custom field
            "pincode": pincode,                    # Custom field
            "country": country_iso,
            "notes": notes,
            "source": "IndiaMART",
            "status": "Open"
        })

        # Add custom fields if they exist in Lead doctype
        if hasattr(lead, "custom_query_time"):
            lead.custom_query_time = query_time
        if hasattr(lead, "custom_query_type"):
            lead.custom_query_type = query_type
        if hasattr(lead, "custom_product_name"):
            lead.custom_product_name = product_name
        if hasattr(lead, "custom_unique_query_id"):
            lead.custom_unique_query_id = unique_query_id
        if hasattr(lead, "custom_call_duration"):
            lead.custom_call_duration = call_duration

        lead.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger().info(f"IndiaMART Lead created: {lead_name} - {mobile}")

        # ----- Optional: Additional automation (uncomment as needed) -----
        # assign_sales_person(lead)
        # customer = create_customer(lead_name, mobile)
        # create_opportunity(customer, lead)
        # send_whatsapp_reply(mobile, lead_name)
        # create_followup(lead)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "IndiaMART PROCESS ERROR")



# import frappe

# def process_lead(data):
#     try:
#         data = frappe._dict(data)

#         # 📌 Field Mapping (IndiaMART varies)
#         lead_name = data.get("name") or data.get("sender_name") or "Unknown"
#         phone = data.get("mobile") or data.get("mobile_no")
#         email = data.get("email")
#         message = data.get("query") or data.get("message")

#         # 🚫 Duplicate Check
#         existing = None
#         if phone:
#             existing = frappe.db.get_value("Lead", {"mobile_no": phone})
#         elif email:
#             existing = frappe.db.get_value("Lead", {"email_id": email})

#         if existing:
#             return

#         # ✅ Create Lead
#         lead = frappe.get_doc({
#             "doctype": "Lead",
#             "lead_name": lead_name,
#             "mobile_no": phone,
#             "email_id": email,
#             "notes": message,
#             "source": "IndiaMART",
#             "status": "Open"
#         })
#         lead.insert(ignore_permissions=True)

#         # 👨‍💼 Assign Sales Person
#         assign_sales_person(lead)

#         # 🧾 Create Customer
#         customer = create_customer(lead_name)

#         # 💰 Create Opportunity
#         create_opportunity(customer)

#         # 💬 WhatsApp Auto Reply
#         send_whatsapp_reply(phone, lead_name)

#         # 📅 Follow-up Task
#         create_followup(lead)

#         frappe.db.commit()

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "IndiaMART PROCESS ERROR")