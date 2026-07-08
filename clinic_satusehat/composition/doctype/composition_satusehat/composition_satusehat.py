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

class CompositionSatuSehat(Document):
	def before_save(self):
		self.generate_payload()

	def after_insert(self):
		validator_name = self.name.replace("COM-SS-", "VAL-COM-")
		doc = frappe.get_doc({
			"doctype": "Composition Validator",
			"name": validator_name,
			"composition_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def generate_payload(self):
		if not self.encounter_satusehat:
			return
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID.")

		sections = []

		# 1. Gather Condition / Diagnosis
		conditions = frappe.get_all("Condition SatuSehat", 
			filters={"encounter_satusehat": self.encounter_satusehat, "status": "Valid"}, 
			fields=["satusehat_id"])
		
		if conditions:
			entry_list = [{"reference": f"Condition/{c.satusehat_id}"} for c in conditions if c.satusehat_id]
			if entry_list:
				sections.append({
					"title": "Diagnosis",
					"code": {
						"coding": [{"system": "http://loinc.org", "code": "11450-4", "display": "Problem list - Reported"}]
					},
					"entry": entry_list
				})

		# 2. Gather Observation / Vital Signs
		observations = frappe.get_all("Observation SatuSehat", 
			filters={"encounter_satusehat": self.encounter_satusehat, "status": "Valid"}, 
			fields=["satusehat_ids"])
		
		obs_entry_list = []
		for obs in observations:
			if obs.satusehat_ids:
				ids = [i.strip() for i in obs.satusehat_ids.split(",") if i.strip()]
				for i in ids:
					obs_entry_list.append({"reference": f"Observation/{i}"})
		
		if obs_entry_list:
			sections.append({
				"title": "Vital Signs",
				"code": {
					"coding": [{"system": "http://loinc.org", "code": "8716-3", "display": "Vital signs"}]
				},
				"entry": obs_entry_list
			})

		# 3. Gather Procedure / Tindakan
		procedures = frappe.get_all("Procedure SatuSehat", 
			filters={"encounter_satusehat": self.encounter_satusehat, "status": "Valid"}, 
			fields=["satusehat_id"])
		
		if procedures:
			proc_entry_list = [{"reference": f"Procedure/{p.satusehat_id}"} for p in procedures if p.satusehat_id]
			if proc_entry_list:
				sections.append({
					"title": "Procedure",
					"code": {
						"coding": [{"system": "http://loinc.org", "code": "47519-4", "display": "History of Procedures Document"}]
					},
					"entry": proc_entry_list
				})

		payload = {
			"resourceType": "Composition",
			"status": "final",
			"type": {
				"coding": [
					{
						"system": "http://loinc.org",
						"code": "18842-5",
						"display": "Discharge summary"
					}
				]
			},
			"subject": {
				"reference": f"Patient/{self.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{self.satusehat_encounter_id}"
			},
			"date": datetime.now().isoformat() + "+07:00",
			"author": [
				{
					"reference": f"Practitioner/{self.practitioner_ihs}"
				}
			],
			"title": self.composition_title or "Resume Medis",
			"section": sections
		}

		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Composition SatuSehat", docname)
	if not doc.payload_json:
		frappe.throw("Silakan Save dokumen terlebih dahulu untuk membuat payload!")

	payload = json.loads(doc.payload_json)

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	endpoint = f"{base_url}/Composition"
	headers = _satusehat_headers()

	try:
		resp = requests.post(endpoint, json=payload, headers=headers, timeout=60)
		res_data = {"status_code": resp.status_code, "response": resp.text}
		
		frappe.db.set_value("Composition SatuSehat", doc.name, "api_response", json.dumps(res_data, indent=4))
		
		if resp.status_code in [200, 201]:
			try:
				r_json = resp.json()
				if "id" in r_json:
					frappe.db.set_value("Composition SatuSehat", doc.name, "satusehat_id", r_json["id"])
					frappe.db.set_value("Composition SatuSehat", doc.name, "status", "Valid")
			except: pass
			frappe.db.commit()
			return {"status": 201}
		else:
			frappe.db.set_value("Composition SatuSehat", doc.name, "status", "Rejected")
			frappe.db.commit()
			return {"status": 400}
	except Exception as e:
		res_data = {"error": str(e)}
		frappe.db.set_value("Composition SatuSehat", doc.name, "api_response", json.dumps(res_data, indent=4))
		frappe.db.set_value("Composition SatuSehat", doc.name, "status", "Rejected")
		frappe.db.commit()
		return {"status": 400}
