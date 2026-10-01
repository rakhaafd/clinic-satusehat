import frappe

def setup():
    doctors = frappe.get_all("Healthcare Practitioner", pluck="name")
    for doc_name in doctors:
        doc = frappe.get_doc("Healthcare Practitioner", doc_name)
        # Clear existing
        doc.custom_accepted_payment_methods = []
        
        # We can add a few modes. Let's add Cash, BPJS, Insurance, Company Guarantee
        # Cash is standard. Let's add some variety.
        modes = ["Cash", "BPJS"]
        if "Alexander" in doc.practitioner_name:
            modes = ["Cash", "Company Guarantee"]
        elif "Olivia" in doc.practitioner_name:
            modes = ["Cash", "Insurance", "BPJS"]
            
        for m in modes:
            if frappe.db.exists("Mode of Payment", m):
                doc.append("custom_accepted_payment_methods", {
                    "mode_of_payment": m
                })
        
        # Skip mandatory checks and save
        doc.flags.ignore_mandatory = True
        doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("Updated doctors")

