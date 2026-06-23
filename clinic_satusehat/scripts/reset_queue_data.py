import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    print("Resetting all Queue Tickets...")
    
    ticket_types = [
        "Pharmacy Queue Ticket",
        "Clinic Queue Ticket",
        "Registration Queue Ticket"
    ]

    for doctype in ticket_types:
        docs = frappe.get_all(doctype)
        for d in docs:
            frappe.delete_doc(doctype, d.name, ignore_permissions=True, force=1)
        print(f"Deleted {len(docs)} records from {doctype}")

    frappe.db.commit()
    print("Reset complete! Your queue is now empty.")
