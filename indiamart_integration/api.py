import frappe

@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):
    try:
        # 🔐 Secret Token (site_config se)
        SECRET = frappe.conf.get("indiamart_secret")

        if SECRET and kwargs.get("token") != SECRET:
            return {"status": "unauthorized"}

        # 🧪 Debug (initial days only)
        frappe.log_error(str(kwargs), "IndiaMART RAW DATA")

        # ✅ Basic Validation
        if not kwargs.get("mobile") and not kwargs.get("mobile_no"):
            return {"status": "error", "message": "Mobile is required"}

        # ⚡ Background Job (fast response)
        frappe.enqueue(
            "indiamart_integration.services.lead_service.process_lead",
            queue="short",
            timeout=300,
            data=kwargs
        )

        return {"status": "queued"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "IndiaMART API ERROR")
        return {"status": "error", "message": str(e)}