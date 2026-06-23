import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    # Create Custom Field 'encounter_ref'
    create_custom_field("Clinic Queue Ticket", {
        "fieldname": "encounter_ref",
        "label": "Patient Encounter",
        "fieldtype": "Link",
        "options": "Patient Encounter",
        "insert_after": "practitioner",
        "read_only": 1
    })
    
    frappe.db.commit()
    print("Added encounter_ref field.")
