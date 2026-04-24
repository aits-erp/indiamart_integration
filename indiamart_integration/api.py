import frappe

@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):
    try:
        # Log only keys to avoid truncation error
        frappe.logger().info(f"IndiaMART webhook keys: {list(kwargs.keys())}")
        
        # Extract the actual lead data (IndiaMART nests it under "RESPONSE")
        lead_data = kwargs.get("RESPONSE") or kwargs
        
        # Log a preview (first 200 chars of the extracted data)
        frappe.log_error(str(lead_data)[:200], "IndiaMART Lead Data Preview")

        # Extract mobile from various possible fields
        mobile = (
            lead_data.get("mobile") or
            lead_data.get("mobile_no") or
            lead_data.get("SENDER_MOBILE")
        )
        if not mobile:
            # Also check if it's inside a nested "response" (lowercase)
            if isinstance(kwargs.get("response"), dict):
                mobile = kwargs["response"].get("SENDER_MOBILE")
            if not mobile:
                return {"status": "error", "message": "Mobile is required"}

        # Normalize mobile (remove +91, spaces, dashes)
        mobile = mobile.replace("+91", "").replace("-", "").replace(" ", "").strip()
        lead_data["unified_mobile"] = mobile

        # Enqueue background job with the full data (including original structure)
        frappe.enqueue(
            "indiamart_integration.services.lead_service.process_lead",
            queue="short",
            timeout=300,
            data=lead_data  # pass the actual lead data, not the wrapper
        )

        return {"status": "queued"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "IndiaMART API ERROR")
        return {"status": "error", "message": str(e)}