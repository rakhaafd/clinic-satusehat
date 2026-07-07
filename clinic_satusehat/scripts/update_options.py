import json

filepath = "apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator/satusehat_payload_generator.json"
with open(filepath, "r") as f:
    data = json.load(f)

for field in data.get("fields", []):
    if field.get("fieldname") == "resource_type":
        field["options"] = "Encounter\nCondition\nObservation\nProcedure\nComposition\nMedication\nMedicationRequest"
        break

with open(filepath, "w") as f:
    json.dump(data, f, indent=1)

print("Updated resource_type options")
