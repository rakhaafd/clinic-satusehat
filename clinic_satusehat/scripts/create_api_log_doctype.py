import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    doctype_name = "SatuSehat API Log"
    if not frappe.db.exists("DocType", doctype_name):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": doctype_name,
            "module": "Queue Core",
            "custom": 1,
            "autoname": "LOG-.YYYY.-.MM.-.DD.-.####",
            "naming_rule": "Expression",
            "editable_grid": 1,
            "in_create": 1,
            "fields": [
                {
                    "fieldname": "reference_doc",
                    "label": "Reference Doc",
                    "fieldtype": "Link",
                    "options": "SatuSehat Payload Generator",
                    "in_list_view": 1
                },
                {
                    "fieldname": "resource_type",
                    "label": "Resource Type",
                    "fieldtype": "Data",
                    "in_list_view": 1
                },
                {
                    "fieldname": "satusehat_id",
                    "label": "SatuSehat ID",
                    "fieldtype": "Data",
                    "in_list_view": 1
                },
                {
                    "fieldname": "status_code",
                    "label": "Status Code",
                    "fieldtype": "Int",
                    "in_list_view": 1
                },
                {
                    "fieldname": "response_json",
                    "label": "Response JSON",
                    "fieldtype": "Code",
                    "options": "JSON"
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                }
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"DocType {doctype_name} created successfully.")
    else:
        print(f"DocType {doctype_name} already exists.")
