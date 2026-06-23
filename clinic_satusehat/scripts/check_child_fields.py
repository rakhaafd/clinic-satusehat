import frappe
import json

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    child_tables = [
        'Patient Encounter Symptom',
        'Patient Encounter Diagnosis',
        'Drug Prescription',
        'Procedure Prescription'
    ]

    for dt in child_tables:
        print(f"\n--- {dt} ---")
        fields = frappe.get_all('DocField', 
            filters={'parent': dt}, 
            fields=['fieldname', 'label', 'fieldtype', 'options']
        )
        for f in fields:
            print(f"{f['label']} ({f['fieldname']}) - {f['fieldtype']}")
