import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()
    fields = frappe.get_meta('Medication').fields
    print("Link Fields in Medication:")
    for f in fields:
        if f.fieldtype == 'Link':
            print(f"- {f.label} ({f.fieldname}) -> Options: {f.options}")
