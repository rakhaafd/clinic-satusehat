import frappe

def create_custom_fields():
    custom_fields = {
        "Sales Invoice": [
            {
                "fieldname": "patient",
                "label": "Patient",
                "fieldtype": "Link",
                "options": "Patient",
                "insert_after": "customer",
                "read_only": 0
            },
            {
                "fieldname": "service_unit",
                "label": "Service Unit",
                "fieldtype": "Link",
                "options": "Healthcare Service Unit",
                "insert_after": "patient",
                "read_only": 0
            },
            {
                "fieldname": "ref_practitioner",
                "label": "Referring Practitioner",
                "fieldtype": "Link",
                "options": "Healthcare Practitioner",
                "insert_after": "service_unit",
                "read_only": 0
            }
        ],
        "Sales Invoice Item": [
            {
                "fieldname": "reference_dt",
                "label": "Reference DocType",
                "fieldtype": "Link",
                "options": "DocType",
                "insert_after": "item_code",
                "read_only": 0
            },
            {
                "fieldname": "reference_dn",
                "label": "Reference Name",
                "fieldtype": "Dynamic Link",
                "options": "reference_dt",
                "insert_after": "reference_dt",
                "read_only": 0
            }
        ]
    }

    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(custom_fields)
    print("Custom Fields berhasil dibuat/diperbarui!")

def run():
    print("Mulai membuat Custom Field...")
    create_custom_fields()
