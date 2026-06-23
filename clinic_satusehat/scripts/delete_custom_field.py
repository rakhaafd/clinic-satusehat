import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    if frappe.db.exists('Custom Field', 'Clinic Queue Ticket-encounter_ref'):
        frappe.delete_doc('Custom Field', 'Clinic Queue Ticket-encounter_ref', ignore_permissions=True, force=1)
        frappe.db.commit()
        print("Deleted Custom Field")
    else:
        print("Custom field not found")
