import frappe

def check_vital_signs():
    print("\nVital Signs fields:")
    try:
        for f in frappe.get_meta("Vital Signs").fields:
            print(f"{f.fieldname} ({f.fieldtype})")
    except Exception as e:
        pass
