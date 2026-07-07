import json

filepath = "apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator/satusehat_payload_generator.json"
with open(filepath, "r") as f:
    data = json.load(f)

unique_perms = []
seen_roles = set()

for perm in data.get("permissions", []):
    role = perm.get("role")
    level = perm.get("permlevel", 0)
    key = f"{role}-{level}"
    
    if key not in seen_roles:
        unique_perms.append(perm)
        seen_roles.add(key)

data["permissions"] = unique_perms

with open(filepath, "w") as f:
    json.dump(data, f, indent=1)

print("Removed duplicate permissions")
