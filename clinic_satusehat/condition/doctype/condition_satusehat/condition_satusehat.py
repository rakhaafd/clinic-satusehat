# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
import requests

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

class ConditionSatuSehat(Document):
	def before_save(self):
		self.set_icd_code()
		self.generate_payload()
		
	def after_insert(self):
		validator_name = self.name.replace("CND-SS-", "VAL-CND-")
		doc = frappe.get_doc({
			"doctype": "Condition Validator",
			"name": validator_name,
			"condition_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def set_icd_code(self):
		if not self.icd_code and self.patient_encounter:
			encounter_doc = frappe.get_doc("Patient Encounter", self.patient_encounter)
			if encounter_doc.diagnosis:
				first_diagnosis = encounter_doc.diagnosis[0]
				if first_diagnosis.diagnosis:
					try:
						diag = frappe.get_doc("Diagnosis", first_diagnosis.diagnosis)
						self.icd_code = diag.get("icd10_code") or diag.get("diagnosis_code")
						self.diagnosis_display = diag.get("diagnosis_name") or diag.get("description")
					except:
						pass

		if not self.icd_code:
			frappe.throw("Mohon isi ICD-10 Code untuk Diagnosis ini.")

		if not self.diagnosis_display:
			self.diagnosis_display = "Diagnosis"

	def generate_payload(self):
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID. Pastikan Encounter sudah sukses dikirim.")
			
		payload = {
			"resourceType": "Condition",
			"clinicalStatus": {
				"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active", "display": "Active"}]
			},
			"category": [
				{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis", "display": "Encounter Diagnosis"}]}
			],
			"code": {
				"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": self.icd_code, "display": self.diagnosis_display}]
			},
			"subject": {"reference": f"Patient/{self.patient_ihs or 'GANTI_DENGAN_IHS_PASIEN'}", "display": self.patient_name},
			"encounter": {"reference": f"Encounter/{self.satusehat_encounter_id}"}
		}
		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Condition SatuSehat", docname)
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
		frappe.db.set_value("Condition SatuSehat", doc.name, "api_response", result_str)

		satusehat_id = ""
		if resp.status_code in [200, 201]:
			try:
				resp_json = resp.json()
				if "id" in resp_json:
					satusehat_id = resp_json["id"]
					frappe.db.set_value("Condition SatuSehat", doc.name, "satusehat_id", satusehat_id)
			except: pass

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
		frappe.db.set_value("Condition SatuSehat", doc.name, "api_response", str(e))
		frappe.db.commit()
		return {"status": 500, "message": str(e)}
