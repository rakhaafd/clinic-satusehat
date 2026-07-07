import frappe

def check_field():
    f = frappe.get_meta('Vital Signs').get_field('encounter')
    print("Field properties:")
    print("hidden:", f.hidden)
    print("depends_on:", f.depends_on)
    print("mandatory:", f.reqd)
