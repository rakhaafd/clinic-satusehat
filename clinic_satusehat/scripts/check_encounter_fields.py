import frappe
import json

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    fields = frappe.get_all('DocField', 
        filters={'parent': 'Patient Encounter'}, 
        fields=['fieldname', 'label', 'fieldtype', 'options']
    )
    
    for f in fields:
        print(f"{f['label']} ({f['fieldname']}) - {f['fieldtype']} - {f['options']}")
