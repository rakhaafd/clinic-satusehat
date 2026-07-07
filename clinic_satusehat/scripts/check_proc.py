import frappe
def get_template_fields():
    for f in frappe.get_meta('Clinical Procedure Template').fields:
        print(f.fieldname, getattr(f, 'fieldtype', ''))
