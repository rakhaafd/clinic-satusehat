import json

filepath = "apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator/satusehat_payload_generator.json"
with open(filepath, "r") as f:
    data = json.load(f)

# Find resource_type
idx = 0
for i, field in enumerate(data.get("fields", [])):
    if field.get("fieldname") == "resource_type":
        idx = i
        break

new_field = {
    "fieldname": "patient_encounter",
    "fieldtype": "Link",
    "options": "Patient Encounter",
    "label": "Tarik Data dari Kunjungan (Patient Encounter)",
    "description": "Pilih kunjungan untuk otomatis mengisi IHS Pasien dan Dokter"
}

# insert if not exists
if not any(f.get("fieldname") == "patient_encounter" for f in data["fields"]):
    data["fields"].insert(idx + 1, new_field)
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=1)
        
    print("Modified JSON")
else:
    print("Field already exists")
