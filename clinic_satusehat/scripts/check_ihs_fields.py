import frappe

def get_fields():
    print("Patient fields:")
    for f in frappe.get_meta("Patient").fields:
        if "ihs" in f.fieldname.lower() or "satusehat" in f.fieldname.lower():
            print(f.fieldname)
            
    print("\nPractitioner fields:")
    for f in frappe.get_meta("Healthcare Practitioner").fields:
        if "ihs" in f.fieldname.lower() or "satusehat" in f.fieldname.lower():
            print(f.fieldname)
