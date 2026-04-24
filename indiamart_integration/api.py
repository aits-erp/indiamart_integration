import frappe

@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):
    try:
        # 🧪 Debug – log safely, avoid truncation
        frappe.logger().info(f"IndiaMART webhook keys: {list(kwargs.keys())}")
        frappe.log_error(str(kwargs)[:200], "IndiaMART RAW DATA (preview)")

        # ✅ Basic Validation – support all possible mobile fields
        mobile = (
            kwargs.get("mobile") or 
            kwargs.get("mobile_no") or 
            kwargs.get("SENDER_MOBILE")
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