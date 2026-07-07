import frappe
def get_fields():
    for f in frappe.get_meta('Drug Prescription').fields:
        print(f.fieldname)

