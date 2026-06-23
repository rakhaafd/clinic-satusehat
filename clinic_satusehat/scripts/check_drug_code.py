import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()
    
    doctypes_to_check = ['Drug Prescription', 'Medication', 'Item']
    
    for dt in doctypes_to_check:
        try:
            fields = frappe.get_meta(dt).fields
            print(f"\n--- Fields in {dt} ---")
            for f in fields:
                if 'drug' in f.fieldname.lower() or 'item' in f.fieldname.lower() or f.reqd:
                    print(f"- {f.label} ({f.fieldname}) [{f.fieldtype}] Reqd: {f.reqd} Options: {f.options}")
        except Exception as e:
            print(f"Could not get {dt}: {e}")
