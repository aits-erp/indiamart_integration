import frappe
import json


def get_or_create_customer(customer_name, mobile):

    existing_customer = frappe.db.get_value(
        "Customer",
        {"mobile_no": mobile},
        "name"
    )

    if existing_customer:
        return existing_customer

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": "Individual",
        "mobile_no": mobile
    })

    customer.insert(ignore_permissions=True)
    frappe.db.commit()

    return customer.name


def create_lead(data, mobile):

    lead_name = (
        data.get("SENDER_NAME")
        or data.get("sender_name")
        or "Unknown"
    )

    email = (
        data.get("SENDER_EMAIL")
        or data.get("sender_email")
        or ""
    )

    message = (
        data.get("QUERY_MESSAGE")
        or data.get("query_message")
        or ""
    )

    product = (
        data.get("QUERY_PRODUCT_NAME")
        or data.get("query_product_name")
        or data.get("PRODUCT_NAME")
        or ""
    )

    qty = (
        data.get("QUANTITY")
        or data.get("quantity")
        or data.get("QTY")
        or ""
    )

    value = (
        data.get("VALUE")
        or data.get("value")
        or data.get("ORDER_VALUE")
        or ""
    )

    company_name = (
        data.get("COMPANY_NAME")
        or data.get("GLUSR_USR_COMPANYNAME")
        or ""
    )

    no_of_employees = (
        data.get("EMPLOYEE_COUNT")
        or data.get("NO_OF_EMPLOYEES")
        or ""
    )

    gst_no = (
        data.get("GST_NO")
        or data.get("GSTIN")
        or ""
    )

    address_html = (
        data.get("SENDER_ADDRESS")
        or data.get("ADDRESS")
        or ""
    )

    qualification_status = (
        data.get("QUALIFICATION_STATUS")
        or ""
    )

    campaign_name = (
        data.get("QUERY_SOURCE")
        or data.get("CAMPAIGN_NAME")
        or ""
    )

    existing_lead = frappe.db.get_value(
        "Lead",
        {"mobile_no": mobile},
        "name"
    )

    if existing_lead:
        return existing_lead

    lead = frappe.get_doc({
        "doctype": "Lead",
        "lead_name": lead_name,
        "mobile_no": mobile,
        "email_id": email,

        "company_name": company_name,
        "no_of_employees": no_of_employees,
        "custom_gst_no": gst_no,
        "address_html": address_html,
        "custom_address": address_html,
        "qualification_status": qualification_status,
        "campaign_name": campaign_name,
        "company": company_name,

        "description": f"""
Product: {product}
Quantity: {qty}
Value: {value}

Message:
{message}
"""
    })

    # Child Table Row
    lead.append("custom_product_details", {
        "item": product,
        "qty": qty,
        "value": value
    })

    lead.insert(ignore_permissions=True)

    frappe.db.commit()

    return lead.name


# def create_lead(data, mobile):

#     lead_name = (
#         data.get("SENDER_NAME")
#         or data.get("sender_name")
#         or "Unknown"
#     )

#     email = (
#         data.get("SENDER_EMAIL")
#         or data.get("sender_email")
#         or ""
#     )

#     message = (
#         data.get("QUERY_MESSAGE")
#         or data.get("query_message")
#         or ""
#     )

#     product = (
#         data.get("QUERY_PRODUCT_NAME")
#         or data.get("query_product_name")
#         or data.get("PRODUCT_NAME")
#         or ""
#     )

#     qty = (
#         data.get("QUANTITY")
#         or data.get("quantity")
#         or data.get("QTY")
#         or ""
#     )

#     value = (
#         data.get("VALUE")
#         or data.get("value")
#         or data.get("ORDER_VALUE")
#         or ""
#     )


#     # ---------------------------------------------------
#     # CHECK EXISTING LEAD
#     # ---------------------------------------------------

#     existing_lead = frappe.db.get_value(
#         "Lead",
#         {"mobile_no": mobile},
#         "name"
#     )

#     if existing_lead:
#         return existing_lead

#     # ---------------------------------------------------
#     # CREATE LEAD
#     # ---------------------------------------------------

#     lead = frappe.get_doc({
#         "doctype": "Lead",
#         "lead_name": lead_name,
#         "mobile_no": mobile,
#         "email_id": email,
#        # Custom Fields
#         "custom_product_name": product,
#         "custom_qty": qty,
#         "custom_value": value,
#         # IMPORTANT:
#         # use normal text field only
#         # do NOT use child table fields
#         "description": f"""
# Product: {product}
# Quantity: {qty}
# Value: {value}
# Message:
# {message}
# """
#     })

#     lead.insert(ignore_permissions=True)

#     frappe.db.commit()

#     return lead.name


@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):

    try:

        frappe.logger().info(f"IndiaMART Payload: {kwargs}")

        # ---------------------------------------------------
        # RESPONSE WRAPPER
        # ---------------------------------------------------

        lead_data = kwargs.get("RESPONSE")

        if isinstance(lead_data, str):
            lead_data = json.loads(lead_data)

        if not lead_data:
            lead_data = kwargs

        # ---------------------------------------------------
        # MOBILE
        # ---------------------------------------------------

        mobile = (
            lead_data.get("SENDER_MOBILE")
            or lead_data.get("mobile")
            or lead_data.get("mobile_no")
            or ""
        )

        if not mobile:

            frappe.log_error(
                title="IndiaMART Missing Mobile",
                message=json.dumps(lead_data, indent=2)
            )

            return {
                "status": "error",
                "message": "Mobile is required"
            }

        # Normalize mobile
        mobile = str(mobile)

        mobile = (
            mobile.replace("+91", "")
            .replace("-", "")
            .replace(" ", "")
            .strip()
        )

        # ---------------------------------------------------
        # CUSTOMER NAME
        # ---------------------------------------------------

        customer_name = (
            lead_data.get("SENDER_NAME")
            or lead_data.get("sender_name")
            or "Unknown"
        )

        # ---------------------------------------------------
        # CUSTOMER
        # ---------------------------------------------------

        customer = get_or_create_customer(
            customer_name,
            mobile
        )

        # ---------------------------------------------------
        # LEAD
        # ---------------------------------------------------

        lead = create_lead(
            lead_data,
            mobile
        )

        return {
            "status": "success",
            "customer": customer,
            "lead": lead,
            "mobile": mobile
        }

    except Exception as e:

        frappe.log_error(
            frappe.get_traceback(),
            "IndiaMART API ERROR"
        )

        return {
            "status": "error",
            "message": str(e)
        }
# import frappe

# @frappe.whitelist(allow_guest=True)
# def webhook(**kwargs):
#     try:
#         # IndiaMART sends data inside {"RESPONSE": {...}}
#         lead_data = kwargs.get("RESPONSE") or kwargs
#         mobile = lead_data.get("SENDER_MOBILE") or lead_data.get("mobile") or lead_data.get("mobile_no")
#         if not mobile:
#             return {"status": "error", "message": "Mobile is required"}
#         # Normalise
#         mobile = mobile.replace("+91", "").replace("-", "").replace(" ", "").strip()
#         lead_data["unified_mobile"] = mobile

#         frappe.enqueue(
#             "indiamart_integration.services.lead_service.process_lead",
#             queue="short",
#             timeout=300,
#             data=lead_data
#         )
#         return {"status": "queued"}
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "IndiaMART API ERROR")
#         return {"status": "error", "message": str(e)}
