import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    doctypes = [
        "Registration Queue Ticket",
        "Clinic Queue Ticket",
        "Pharmacy Queue Ticket",
        "Patient Encounter"
    ]

    total_deleted = 0

    # 1. Delete all records
    for dt in doctypes:
        records = frappe.get_all(dt, pluck="name")
        for name in records:
            try:
                # If the document is submittable, cancel it first
                doc = frappe.get_doc(dt, name)
                if getattr(doc, "docstatus", 0) == 1:
                    doc.cancel()
                
                frappe.delete_doc(dt, name, ignore_permissions=True, force=True)
                total_deleted += 1
            except frappe.LinkExistsError:
                # Bypass link check for Patient Encounter by forcing SQL delete
                if dt == "Patient Encounter":
                    frappe.db.sql(f"DELETE FROM `tab{dt}` WHERE name=%s", (name,))
                    total_deleted += 1
                    print(f"Force deleted {dt} {name} via SQL due to existing links.")
            except Exception as e:
                # Catch general exceptions (including LinkExistsError if not caught above)
                if dt == "Patient Encounter" and "linked with" in str(e):
                    frappe.db.sql(f"DELETE FROM `tab{dt}` WHERE name=%s", (name,))
                    total_deleted += 1
                    print(f"Force deleted {dt} {name} via SQL due to existing links.")
                else:
                    print(f"Error deleting {dt} {name}: {e}")
        
        print(f"Deleted {len(records)} records from {dt}.")

    # 2. Reset the naming series so the next one starts at 0001
    series_prefixes = ["REG-", "POLI-", "APT-", "HLC-ENC-"]
    
    for prefix in series_prefixes:
        frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s", (prefix + "%",))
        print(f"Reset naming series for {prefix}")

    frappe.db.commit()
    print(f"\nSuccessfully flushed {total_deleted} records and reset counters to 1.")
