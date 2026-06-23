import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    try:
        if frappe.db.exists('Medication Request', 'HMR-00001'):
            frappe.delete_doc('Medication Request', 'HMR-00001', ignore_permissions=True, force=1)
            frappe.db.commit()
            print("Deleted Medication Request HMR-00001")
        else:
            print("Medication Request HMR-00001 not found.")
    except Exception as e:
        print(f"Error: {e}")
