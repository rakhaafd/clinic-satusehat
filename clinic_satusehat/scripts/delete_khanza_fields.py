import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    fields = frappe.get_all('Custom Field', 
        fields=['name', 'dt', 'fieldname']
    )
    
    count = 0
    for f in fields:
        if 'khanza' in f.dt.lower() or 'khanza' in f.fieldname.lower() or 'khanza' in f.name.lower():
            try:
                frappe.delete_doc('Custom Field', f.name, ignore_permissions=True, force=1)
                print(f"Deleted: {f.name}")
                count += 1
            except Exception as e:
                print(f"Failed to delete {f.name}: {e}")

    frappe.db.commit()
    print(f"Successfully deleted {count} khanza custom fields.")
