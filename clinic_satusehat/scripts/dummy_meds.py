import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()
    try:
        # Create UOM if not exists
        for uom in ["mg", "ml"]:
            if not frappe.db.exists("UOM", uom):
                frappe.get_doc({
                    "doctype": "UOM",
                    "uom_name": uom
                }).insert(ignore_permissions=True)
                
        medications = [
            {
                "doctype": "Medication",
                "generic_name": "Paracetamol",
                "dosage_form": "Tablet",
                "strength": 500.0,
                "strength_uom": "mg"
            },
            {
                "doctype": "Medication",
                "generic_name": "Amoxicillin",
                "dosage_form": "Tablet",
                "strength": 500.0,
                "strength_uom": "mg"
            },
            {
                "doctype": "Medication",
                "generic_name": "Obat Batuk Hitam",
                "dosage_form": "Syrup",
                "strength": 100.0,
                "strength_uom": "ml"
            }
        ]
        
        for med in medications:
            if not frappe.db.exists("Medication", {"generic_name": med["generic_name"]}):
                doc = frappe.get_doc(med)
                doc.insert(ignore_permissions=True)
                print(f"Created Medication: {med['generic_name']}")
            else:
                print(f"Medication already exists: {med['generic_name']}")
        
        frappe.db.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        frappe.destroy()
