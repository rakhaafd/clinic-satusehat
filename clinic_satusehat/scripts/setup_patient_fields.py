import frappe

def create_patient_custom_field():
    custom_fields = {
        "Patient": [
            {
                "fieldname": "satusehat_id",
                "label": "SatuSehat IHS Number",
                "fieldtype": "Data",
                "insert_after": "uid",
                "read_only": 0,
                "description": "Nomor IHS dari SatuSehat Kemenkes (Contoh: P02478375538)"
            }
        ]
    }

    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(custom_fields)
    print("Custom Field 'SatuSehat IHS Number' berhasil dibuat pada DocType Patient!")

def run():
    create_patient_custom_field()
