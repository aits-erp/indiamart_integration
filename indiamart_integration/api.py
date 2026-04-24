import frappe

@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):
    try:
        # IndiaMART sends data inside {"RESPONSE": {...}}
        lead_data = kwargs.get("RESPONSE") or kwargs
        mobile = lead_data.get("SENDER_MOBILE") or lead_data.get("mobile") or lead_data.get("mobile_no")
        if not mobile:
            return {"status": "error", "message": "Mobile is required"}
        # Normalise
        mobile = mobile.replace("+91", "").replace("-", "").replace(" ", "").strip()
        lead_data["unified_mobile"] = mobile

        frappe.enqueue(
            "indiamart_integration.services.lead_service.process_lead",
            queue="short",
            timeout=300,
            data=lead_data
        )
        return {"status": "queued"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "IndiaMART API ERROR")
        return {"status": "error", "message": str(e)}