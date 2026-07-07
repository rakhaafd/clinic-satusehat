import frappe

def execute():
    doc = frappe.get_doc("DocType", "SatuSehat API Log")
    doc.custom = 0
    doc.save()
    frappe.db.commit()
    print("Converted to Standard DocType")
