import json

filepath = "apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator/satusehat_payload_generator.json"
with open(filepath, "r") as f:
    data = json.load(f)

for field in data.get("fields", []):
    if field.get("fieldname") in ["patient_ihs", "practitioner_ihs"]:
        if "default" in field:
            del field["default"]

with open(filepath, "w") as f:
    json.dump(data, f, indent=1)

print("Removed default values")
