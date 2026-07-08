import frappe
import requests
import json

def _satusehat_headers():
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

@frappe.whitelist()
def register_item_medication(item_code):
	item = frappe.get_doc("Item", item_code)
	if not item.kfa_code:
		frappe.throw("Mohon isi KFA Code terlebih dahulu di Item ini.")

	if item.satusehat_id:
		return {"status": "success", "satusehat_id": item.satusehat_id, "message": "Item ini sudah memiliki SatuSehat ID."}

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	org_id = frappe.conf.get("satusehat_organization_id")
	headers = _satusehat_headers()

	medication_payload = {
		"resourceType": "Medication",
		"meta": {
			"profile": [
				"https://fhir.kemkes.go.id/r4/StructureDefinition/Medication"
			]
		},
		"extension": [
			{
				"url": "https://fhir.kemkes.go.id/r4/StructureDefinition/MedicationType",
				"valueCodeableConcept": {
					"coding": [
						{
							"system": "http://terminology.kemkes.go.id/CodeSystem/medication-type",
							"code": "NC",
							"display": "Non-compound"
						}
					]
				}
			}
		],
		"identifier": [
			{
				"system": f"http://sys-ids.kemkes.go.id/medication/{org_id}",
				"use": "official",
				"value": item_code
			}
		],
		"code": {
			"coding": [
				{
					"system": "http://sys-ids.kemkes.go.id/kfa",
					"code": item.kfa_code,
					"display": item.kfa_display or item.item_name
				}
			]
		},
		"status": "active"
	}

	try:
		resp = requests.post(f"{base_url}/Medication", json=medication_payload, headers=headers, timeout=30)
		if resp.status_code in [200, 201]:
			med_id = resp.json().get("id")
			item.db_set("satusehat_id", med_id)
			frappe.db.commit()
			return {"status": "success", "satusehat_id": med_id, "message": "Berhasil didaftarkan ke SatuSehat!"}
		else:
			frappe.throw(f"Gagal mendaftarkan Medication: {resp.text}")
	except Exception as e:
		frappe.throw(f"Error API Medication: {str(e)}")
