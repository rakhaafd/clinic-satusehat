import os
import re

file_path = "/home/sachi/intern/frappe/frappe-bench-v15/apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator/satusehat_payload_generator.py"
with open(file_path, "r") as f:
    content = f.read()

# Remove old import
content = re.sub(r'from clinic_satusehat\.khanza_satusehat\.satusehat_client import _satusehat_headers\n', '', content)

# Add local function
new_func = """
def _satusehat_headers():
    import requests
    import frappe
    client_id = frappe.conf.get("satusehat_client_id")
    client_secret = frappe.conf.get("satusehat_client_secret")
    auth_url = frappe.conf.get("satusehat_auth_url") or "https://api-satusehat-stg.dto.kemkes.go.id/oauth2/v1"
    
    token_url = f"{auth_url}/accesstoken?grant_type=client_credentials"
    data = {"client_id": client_id, "client_secret": client_secret}
    
    res = requests.post(token_url, data=data, timeout=10)
    if res.status_code == 200:
        token = res.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    frappe.throw(f"Failed to get SatuSehat Token: {res.text}")

"""

# Insert function before class SatuSehatPayloadGenerator
content = content.replace('class SatuSehatPayloadGenerator(Document):', new_func + '\nclass SatuSehatPayloadGenerator(Document):')

with open(file_path, "w") as f:
    f.write(content)

print("Fixed generator")
