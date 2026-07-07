import frappe

def get_table_fields():
    print("\nPatient Encounter Diagnosis fields:")
    try:
        for f in frappe.get_meta("Patient Encounter Diagnosis").fields:
            print(f"{f.fieldname} ({f.fieldtype})")
    except Exception as e:
        print("Error getting Patient Encounter Diagnosis:", str(e))
        
    print("\nClinical Codification Detail fields:")
    try:
        for f in frappe.get_meta("Clinical Codification Detail").fields:
            print(f"{f.fieldname} ({f.fieldtype})")
    except Exception as e:
        print("Error getting Clinical Codification Detail:", str(e))
