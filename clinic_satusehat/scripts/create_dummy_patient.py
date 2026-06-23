import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    print("Creating Dummy Patients...")
    
    dummy_patients = [
        {"first_name": "Budi", "last_name": "Santoso", "gender": "Male", "blood_group": "A", "status": "Active"},
        {"first_name": "Siti", "last_name": "Aminah", "gender": "Female", "blood_group": "O", "status": "Active"},
        {"first_name": "Andi", "last_name": "Kurniawan", "gender": "Male", "blood_group": "B", "status": "Active"},
    ]

    count = 0
    for data in dummy_patients:
        # Check if exists
        if not frappe.db.exists("Patient", {"first_name": data["first_name"], "last_name": data["last_name"]}):
            doc = frappe.get_doc({
                "doctype": "Patient",
                **data
            })
            doc.insert(ignore_permissions=True)
            count += 1
            print(f"Created: {data['first_name']} {data['last_name']}")
        else:
            print(f"Skipped: {data['first_name']} {data['last_name']} already exists.")

    frappe.db.commit()
    print(f"Successfully added {count} new dummy patients.")
