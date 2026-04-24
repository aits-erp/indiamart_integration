import frappe

@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):
    try:
        # 🔐 Secret Token (site_config se)
        SECRET = frappe.conf.get("indiamart_secret")
        if SECRET and kwargs.get("token") != SECRET:
            return {"status": "unauthorized"}

        # 🧪 Debug – log safely, avoid truncation (max 140 chars)
        # Use frappe.logger() instead of frappe.log_error for large data
        frappe.logger().info(f"IndiaMART webhook keys: {list(kwargs.keys())}")
        # Optional: log a preview (first 200 chars) in Error Log
        frappe.log_error(str(kwargs)[:200], "IndiaMART RAW DATA (preview)")

        # ✅ Basic Validation – support all possible mobile fields
        mobile = (
            kwargs.get("mobile") or 
            kwargs.get("mobile_no") or 
            kwargs.get("SENDER_MOBILE")  # IndiaMART's actual field
        )
        if not mobile:
            return {"status": "error", "message": "Mobile is required"}

        # Normalize mobile (remove +91 if present)
        mobile = mobile.replace("+91", "").strip()
        kwargs["unified_mobile"] = mobile

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