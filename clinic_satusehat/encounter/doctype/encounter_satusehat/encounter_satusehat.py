# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, format_datetime

class EncounterSatuSehat(Document):
	def before_save(self):
		self.set_start_time()
		self.generate_payload()
		
	def after_insert(self):
		# Create Encounter Validator
		validator_name = self.name.replace("ENC-SS-", "VAL-ENC-")
		doc = frappe.get_doc({
			"doctype": "Encounter Validator",
			"name": validator_name,
			"encounter_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)
		
	def set_start_time(self):
		if self.patient_encounter:
			enc = frappe.get_doc("Patient Encounter", self.patient_encounter)
			if enc.encounter_date and enc.encounter_time:
				# Combine date and time
				dt_str = f"{enc.encounter_date} {enc.encounter_time}"
				self.start_time = get_datetime(dt_str)
	
	def generate_payload(self):
		if not self.start_time:
			frappe.throw("Start Time is required. Ensure Patient Encounter has Date and Time.")
		
		# Format to ISO 8601 (Local time with +07:00 or UTC). SatuSehat expects timezone.
		# Frappe's format_datetime(..., "yyyy-MM-dd'T'HH:mm:ss")
		dt = get_datetime(self.start_time)
		iso_time = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00") # Assume UTC for SatuSehat compliance or adjust tz

		# Retrieve standard identifiers from previous payload generator logic
		payload = {
			"resourceType": "Encounter",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/encounter/{self.organization_id}",
					"value": self.patient_encounter or "ENC-001"
				}
			],
			"status": "arrived",
			"statusHistory": [
				{
					"status": "arrived",
					"period": {
						"start": iso_time
					}
				}
			],
			"class": {
				"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
				"code": "AMB",
				"display": "ambulatory"
			},
			"subject": {
				"reference": f"Patient/{self.patient_ihs or 'GANTI_DENGAN_IHS_PASIEN'}",
				"display": self.patient_name
			},
			"participant": [
				{
					"type": [
						{
							"coding": [
								{
									"system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
									"code": "ATND",
									"display": "attender"
								}
							]
						}
					],
					"individual": {
						"reference": f"Practitioner/{self.practitioner_ihs or 'GANTI_DENGAN_IHS_DOKTER'}",
						"display": self.practitioner_name
					}
				}
			],
			"period": {
				"start": iso_time
			},
			"location": [
				{
					"location": {
						"reference": f"Location/{self.location_id}",
						"display": "Ruang Pemeriksaan"
					}
				}
			],
			"serviceProvider": {
				"reference": f"Organization/{self.organization_id}"
			}
		}

		import json
		self.payload_json = json.dumps(payload, indent=4)

def _satusehat_headers():
	import requests
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
def send_to_satusehat(docname):
	import json, requests
	doc = frappe.get_doc("Encounter SatuSehat", docname)
	if not doc.payload_json:
		frappe.throw("Silakan Save dokumen terlebih dahulu untuk membuat payload!")

	payload_json = json.loads(doc.payload_json)
	resource_type = payload_json.get("resourceType")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	endpoint = f"{base_url}/{resource_type}"

	headers = _satusehat_headers()

	try:
		resp = requests.post(endpoint, json=payload_json, headers=headers, timeout=60)
		result_str = f"STATUS CODE: {resp.status_code}\n\n{resp.text}"

		frappe.db.set_value("Encounter SatuSehat", doc.name, "api_response", result_str)

		satusehat_id = ""
		try:
			if resp.status_code in [200, 201]:
				resp_json = resp.json()
				if "id" in resp_json:
					satusehat_id = resp_json["id"]
					frappe.db.set_value("Encounter SatuSehat", doc.name, "satusehat_id", satusehat_id)
		except:
			pass

		# Log to SatuSehat API Log
		log_doc = frappe.get_doc({
			"doctype": "SatuSehat API Log",
			"reference_doctype": doc.doctype,
			"reference_doc": doc.name,
			"resource_type": resource_type,
			"satusehat_id": satusehat_id,
			"status_code": resp.status_code,
			"response_json": resp.text
		})
		log_doc.insert(ignore_permissions=True)

		frappe.db.commit()

		return {"status": resp.status_code, "message": result_str}
	except Exception as e:
		frappe.db.set_value("Encounter SatuSehat", doc.name, "api_response", str(e))
		frappe.db.commit()
		return {"status": 500, "message": str(e)}
