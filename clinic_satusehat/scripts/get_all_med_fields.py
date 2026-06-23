import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()
    fields = frappe.get_meta('Medication').fields
    print("All fields in Medication:")
    for f in fields:
        print(f"- {f.label} ({f.fieldname}) [{f.fieldtype}] -> {f.options}")
