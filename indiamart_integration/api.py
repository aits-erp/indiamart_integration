import frappe
import json

@frappe.whitelist(allow_guest=True)
def webhook(**kwargs):
    try:
        # ✅ Debug full payload
        frappe.logger().info(f"IndiaMART Payload: {kwargs}")

        # ✅ Handle RESPONSE wrapper
        lead_data = kwargs.get("RESPONSE")

        # Sometimes RESPONSE comes as string JSON
        if isinstance(lead_data, str):
            lead_data = json.loads(lead_data)

        # If RESPONSE not found use kwargs directly
        if not lead_data:
            lead_data = kwargs

        # ✅ Get mobile safely
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

        # ✅ Normalize mobile
        mobile = str(mobile)
        mobile = (
            mobile.replace("+91", "")
            .replace("-", "")
            .replace(" ", "")
            .strip()
        )

        lead_data["unified_mobile"] = mobile

        # ✅ Queue background job
        frappe.enqueue(
            "indiamart_integration.services.lead_service.process_lead",
            queue="short",
            timeout=300,
            data=lead_data
        )

        return {
            "status": "queued",
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
