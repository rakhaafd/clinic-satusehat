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

class ObservationSatuSehat(Document):
	def before_save(self):
		self.set_ihs_ids()
		self.generate_payload()
		
	def after_insert(self):
		print("after_insert CALLED!!!")
		validator_name = self.name.replace("OBS-SS-", "VAL-OBS-")
		doc = frappe.get_doc({
			"doctype": "Observation Validator",
			"name": validator_name,
			"observation_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def set_ihs_ids(self):
		if not self.patient_ihs and self.patient:
			try:
				patient_doc = frappe.get_doc("Patient", self.patient)
				self.patient_ihs = patient_doc.custom_ihs_number or "GANTI_DENGAN_IHS_PASIEN"
			except: pass

		if not self.practitioner_ihs and self.encounter_satusehat:
			try:
				encounter_doc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)
				self.practitioner_ihs = encounter_doc.practitioner_ihs or "GANTI_DENGAN_IHS_DOKTER"
			except: pass

	def generate_payload(self):
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID.")
		if not self.vital_signs:
			frappe.throw("Mohon pilih dokumen Vital Signs.")

		vital_doc = frappe.get_doc("Vital Signs", self.vital_signs)
		encounter_doc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)

		patient_ihs = self.patient_ihs or encounter_doc.patient_ihs
		practitioner_ihs = self.practitioner_ihs or encounter_doc.practitioner_ihs

		if not patient_ihs:
			frappe.throw("Data Patient IHS belum lengkap. Harap pastikan Pasien memiliki IHS ID pada Encounter SatuSehat.")
		if not practitioner_ihs:
			frappe.throw("Data Practitioner IHS belum lengkap. Harap pastikan Dokter/Praktisi memiliki IHS ID pada Encounter SatuSehat.")

		# Generate a base observation dictionary
		def make_base(loinc_code, display):
			return {
				"resourceType": "Observation",
				"status": "final",
				"category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
				"code": {"coding": [{"system": "http://loinc.org", "code": loinc_code, "display": display}]},
				"subject": {"reference": f"Patient/{patient_ihs}"},
				"encounter": {"reference": f"Encounter/{self.satusehat_encounter_id}"},
				"performer": [{"reference": f"Practitioner/{practitioner_ihs}"}],
				"effectiveDateTime": datetime.now().isoformat() + "+07:00"
			}

		payloads = []

		# 1. Heart Rate (Nadi)
		if vital_doc.pulse:
			obs = make_base("8867-4", "Heart rate")
			obs["valueQuantity"] = {"value": float(vital_doc.pulse), "unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
			payloads.append(obs)

		# 2. Respiratory Rate
		if vital_doc.respiratory_rate:
			obs = make_base("9279-1", "Respiratory rate")
			obs["valueQuantity"] = {"value": float(vital_doc.respiratory_rate), "unit": "breaths/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
			payloads.append(obs)

		# 3. Body Temperature
		if vital_doc.temperature:
			obs = make_base("8310-5", "Body temperature")
			obs["valueQuantity"] = {"value": float(vital_doc.temperature), "unit": "C", "system": "http://unitsofmeasure.org", "code": "Cel"}
			payloads.append(obs)

		# 4. Blood Pressure (Component)
		if vital_doc.bp_systolic and vital_doc.bp_diastolic:
			obs = make_base("85354-9", "Blood pressure panel with all children optional")
			obs["component"] = [
				{
					"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]},
					"valueQuantity": {"value": float(vital_doc.bp_systolic), "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
				},
				{
					"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}]},
					"valueQuantity": {"value": float(vital_doc.bp_diastolic), "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
				}
			]
			payloads.append(obs)

		if not payloads:
			frappe.throw("Dokumen Vital Signs tidak memiliki data Nadi, Pernapasan, Suhu, atau Tekanan Darah yang valid.")
			
		self.payload_json = json.dumps(payloads, indent=4)


@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Observation SatuSehat", docname)
	if not doc.payload_json:
		frappe.throw("Silakan Save dokumen terlebih dahulu untuk membuat payload!")

	payloads = json.loads(doc.payload_json)
	if not isinstance(payloads, list):
		frappe.throw("Format payload salah (harus berupa array).")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	endpoint = f"{base_url}/Observation"
	headers = _satusehat_headers()

	responses = []
	satusehat_ids = []
	all_success = True

	for p in payloads:
		try:
			resp = requests.post(endpoint, json=p, headers=headers, timeout=60)
			res_data = {"status_code": resp.status_code, "response": resp.text}
			responses.append(res_data)

			if resp.status_code in [200, 201]:
				try:
					r_json = resp.json()
					if "id" in r_json:
						satusehat_ids.append(r_json["id"])
				except: pass
			else:
				all_success = False

			# Log API
			log_doc = frappe.get_doc({
				"doctype": "SatuSehat API Log",
				"reference_doctype": doc.doctype,
				"reference_doc": doc.name,
				"resource_type": "Observation",
				"status_code": resp.status_code,
				"response_json": resp.text
			})
			log_doc.insert(ignore_permissions=True)
		except Exception as e:
			all_success = False
			responses.append({"error": str(e)})

	frappe.db.set_value("Observation SatuSehat", doc.name, "api_response", json.dumps(responses, indent=4))
	if satusehat_ids:
		frappe.db.set_value("Observation SatuSehat", doc.name, "satusehat_ids", ", ".join(satusehat_ids))
	
	frappe.db.commit()

	if all_success:
		return {"status": 201}
	else:
		return {"status": 400}
