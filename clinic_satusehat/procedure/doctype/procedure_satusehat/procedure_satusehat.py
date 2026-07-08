# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
import requests
from datetime import datetime

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

class ProcedureSatuSehat(Document):
	def before_save(self):
		self.set_ihs_ids()
		self.generate_payload()

	def after_insert(self):
		validator_name = self.name.replace("PRO-SS-", "VAL-PRO-")
		doc = frappe.get_doc({
			"doctype": "Procedure Validator",
			"name": validator_name,
			"procedure_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def set_ihs_ids(self):
		if not self.encounter_satusehat:
			return
		enc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)
		self.patient_ihs = enc.patient_ihs
		self.practitioner_ihs = enc.practitioner_ihs
		self.satusehat_encounter_id = enc.satusehat_id

	def generate_payload(self):
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID.")
		if not self.clinical_procedure:
			frappe.throw("Mohon pilih dokumen Clinical Procedure.")
		if not self.procedure_code or not self.procedure_display:
			frappe.throw("Mohon isi Procedure Code dan Procedure Display.")

		encounter_doc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)
		patient_ihs = self.patient_ihs or encounter_doc.patient_ihs
		practitioner_ihs = self.practitioner_ihs or encounter_doc.practitioner_ihs

		if not patient_ihs:
			frappe.throw("Data Patient IHS belum lengkap. Harap pastikan Pasien memiliki IHS ID pada Encounter SatuSehat.")
		if not practitioner_ihs:
			frappe.throw("Data Practitioner IHS belum lengkap. Harap pastikan Dokter/Praktisi memiliki IHS ID pada Encounter SatuSehat.")

		payload = {
			"resourceType": "Procedure",
			"status": "completed",
			"category": {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": "103693007",
						"display": "Diagnostic procedure"
					}
				],
				"text": "Diagnostic procedure"
			},
			"code": {
				"coding": [
					{
						"system": "http://hl7.org/fhir/sid/icd-9-cm",
						"code": self.procedure_code,
						"display": self.procedure_display
					}
				]
			},
			"subject": {
				"reference": f"Patient/{patient_ihs}",
				"display": self.patient_name
			},
			"encounter": {
				"reference": f"Encounter/{self.satusehat_encounter_id}"
			},
			"performer": [
				{
					"actor": {
						"reference": f"Practitioner/{practitioner_ihs}"
					}
				}
			]
		}

		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Procedure SatuSehat", docname)
	if not doc.payload_json:
		frappe.throw("Silakan Save dokumen terlebih dahulu untuk membuat payload!")

	payload = json.loads(doc.payload_json)

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	endpoint = f"{base_url}/Procedure"
	headers = _satusehat_headers()

	try:
		resp = requests.post(endpoint, json=payload, headers=headers, timeout=60)
		res_data = {"status_code": resp.status_code, "response": resp.text}
		
		frappe.db.set_value("Procedure SatuSehat", doc.name, "api_response", json.dumps(res_data, indent=4))
		
		if resp.status_code in [200, 201]:
			try:
				r_json = resp.json()
				if "id" in r_json:
					frappe.db.set_value("Procedure SatuSehat", doc.name, "satusehat_id", r_json["id"])
					frappe.db.set_value("Procedure SatuSehat", doc.name, "status", "Valid")
			except: pass
			frappe.db.commit()
			return {"status": 201}
		else:
			frappe.db.set_value("Procedure SatuSehat", doc.name, "status", "Rejected")
			frappe.db.commit()
			return {"status": 400}
	except Exception as e:
		res_data = {"error": str(e)}
		frappe.db.set_value("Procedure SatuSehat", doc.name, "api_response", json.dumps(res_data, indent=4))
		frappe.db.set_value("Procedure SatuSehat", doc.name, "status", "Rejected")
		frappe.db.commit()
		return {"status": 400}

