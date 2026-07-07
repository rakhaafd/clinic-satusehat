import frappe

def create_practitioner_custom_fields():
    custom_fields = {
        "Healthcare Practitioner": [
            {
                "fieldname": "nik",
                "label": "NIK",
                "fieldtype": "Data",
                "insert_after": "practitioner_name",
                "read_only": 0,
                "description": "Nomor Induk Kependudukan (Contoh: 7209061211900001)"
            },
            {
                "fieldname": "satusehat_id",
                "label": "SatuSehat IHS Number",
                "fieldtype": "Data",
                "insert_after": "nik",
                "read_only": 0,
                "description": "Nomor IHS Dokter/Perawat dari SatuSehat Kemenkes (Contoh: 10009880728)"
            }
        ]
    }

    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(custom_fields)
    print("Custom Field 'NIK' dan 'SatuSehat IHS Number' berhasil dibuat pada DocType Healthcare Practitioner!")

def run():
    create_practitioner_custom_fields()
