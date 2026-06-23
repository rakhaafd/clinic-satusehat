import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    script_name = "Auto-Link Patient Encounter to Clinic Queue Ticket"
    if frappe.db.exists("Server Script", script_name):
        frappe.delete_doc("Server Script", script_name)

    script_content = """
active_ticket = frappe.db.get_value("Clinic Queue Ticket", {
    "patient_name": doc.patient,
    "status": ["in", ["Dipanggil", "Diperiksa"]],
    "encounter_ref": ["in", ["", None]]
}, "name")

if active_ticket:
    frappe.db.set_value("Clinic Queue Ticket", active_ticket, "encounter_ref", doc.name)
    frappe.msgprint(f"Berhasil menautkan rekam medis ini dengan tiket poli: {active_ticket}")
"""

    doc = frappe.get_doc({
        "doctype": "Server Script",
        "name": script_name,
        "script_type": "DocType Event",
        "reference_doctype": "Patient Encounter",
        "doctype_event": "After Save",
        "script": script_content,
        "disabled": 0
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Server Script created successfully.")
