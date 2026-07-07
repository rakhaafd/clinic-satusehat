import frappe

def create_doctype():
    doctype_name = "SatuSehat Payload Generator"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"DocType {doctype_name} already exists.")
        doc = frappe.get_doc("DocType", doctype_name)
    else:
        doc = frappe.new_doc("DocType")
        doc.name = doctype_name
        doc.module = "Queue Core"
        doc.custom = 0
        doc.issingle = 0
        doc.istable = 0
    
    doc.fields = []
    
    # Configuration Section
    doc.append("fields", {"fieldname": "config_section", "fieldtype": "Section Break", "label": "Konfigurasi"})
    doc.append("fields", {
        "fieldname": "resource_type",
        "fieldtype": "Select",
        "label": "Resource Type",
        "options": "Encounter\nCondition\nObservation\nProcedure",
        "reqd": 1
    })
    doc.append("fields", {"fieldname": "organization_id", "fieldtype": "Data", "label": "Organization ID", "default": "832d59a2-aa46-40cd-94de-7831bbda0a34"})
    doc.append("fields", {"fieldname": "location_id", "fieldtype": "Data", "label": "Location ID", "default": "b017aa54-f1df-4ec2-9d84-8823815d7228"})
    doc.append("fields", {"fieldname": "col_break_config", "fieldtype": "Column Break"})
    doc.append("fields", {"fieldname": "patient_ihs", "fieldtype": "Data", "label": "Patient IHS Number", "default": "P02478375538"})
    doc.append("fields", {"fieldname": "practitioner_ihs", "fieldtype": "Data", "label": "Practitioner IHS Number", "default": "10009880728"})
    
    # Reference Section
    doc.append("fields", {"fieldname": "ref_section", "fieldtype": "Section Break", "label": "Referensi Tambahan"})
    doc.append("fields", {"fieldname": "encounter_id", "fieldtype": "Data", "label": "Encounter ID (Dari Kemenkes)"})
    doc.append("fields", {"fieldname": "col_break_ref", "fieldtype": "Column Break"})
    doc.append("fields", {"fieldname": "diagnostic_code", "fieldtype": "Data", "label": "ICD-10 Code (Cth: K04.1)", "default": "K04.1"})
    doc.append("fields", {"fieldname": "observation_value", "fieldtype": "Data", "label": "Nilai Observasi", "default": "120/80"})
    
    # Payload Section
    doc.append("fields", {"fieldname": "payload_section", "fieldtype": "Section Break", "label": "Hasil Generate & Log", "collapsible": 1})
    doc.append("fields", {"fieldname": "generated_payload", "fieldtype": "Code", "label": "Generated FHIR Payload", "options": "JSON", "read_only": 1})
    doc.append("fields", {"fieldname": "api_response", "fieldtype": "Code", "label": "API Response", "options": "JSON", "read_only": 1})
    
    # Permissions
    doc.permissions = []
    doc.append("permissions", {
        "role": "System Manager",
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1
    })
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("DocType Created/Updated successfully")

if __name__ == "__main__":
    create_doctype()
