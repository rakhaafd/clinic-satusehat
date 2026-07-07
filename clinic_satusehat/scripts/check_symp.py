import frappe
def get_symp_fields():
    for f in frappe.get_meta('Patient Encounter Symptom').fields:
        print(f.fieldname)

