import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    doctypes = [
        "Registration Queue Ticket",
        "Clinic Queue Ticket",
        "Pharmacy Queue Ticket"
    ]

    total_deleted = 0

    # 1. Delete all records
    for dt in doctypes:
        records = frappe.get_all(dt, pluck="name")
        for name in records:
            try:
                frappe.delete_doc(dt, name, ignore_permissions=True, force=True)
                total_deleted += 1
            except Exception as e:
                print(f"Error deleting {dt} {name}: {e}")
        
        print(f"Deleted {len(records)} records from {dt}.")

    # 2. Reset the naming series so the next one starts at 0001
    series_prefixes = ["REG-", "POLI-", "APT-"]
    
    for prefix in series_prefixes:
        frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s", (prefix + "%",))
        print(f"Reset naming series for {prefix}")

    frappe.db.commit()
    print(f"\nSuccessfully flushed {total_deleted} tickets and reset counters to 1.")
