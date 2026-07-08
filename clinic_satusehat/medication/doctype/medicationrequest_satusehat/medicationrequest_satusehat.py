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

class MedicationRequestSatuSehat(Document):
	def after_insert(self):
		validator_name = self.name.replace("MED-REQ-", "VAL-MED-")
		doc = frappe.get_doc({
			"doctype": "MedicationRequest Validator",
			"name": validator_name,
			"medication_request_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

@frappe.whitelist()
def fetch_drugs_from_encounter(docname):
	doc = frappe.get_doc("MedicationRequest SatuSehat", docname)
	if not doc.patient_encounter:
		frappe.throw("Mohon pilih Patient Encounter terlebih dahulu.")
	
	enc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
	
	doc.set("items", [])
	
	for drug in enc.drugs:
		item_code = drug.medication or drug.drug_code
		if not item_code: continue

		item_doc = frappe.get_doc("Item", item_code)
		kfa_code = item_doc.kfa_code
		kfa_display = item_doc.kfa_display or item_doc.item_name
		
		dosage_instructions = ""
		if drug.dosage:
			dosage_instructions += drug.dosage
		if drug.period:
			dosage_instructions += f" for {drug.period}"

		doc.append("items", {
			"item_code": item_code,
			"item_name": item_doc.item_name,
			"kfa_code": kfa_code,
			"kfa_display": kfa_display,
			"dosage": dosage_instructions
		})
	
	doc.save(ignore_permissions=True)
	return {"status": "success"}

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("MedicationRequest SatuSehat", docname)
	if not doc.items:
		frappe.throw("Tidak ada obat yang akan dikirim.")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	org_id = frappe.conf.get("satusehat_organization_id")
	headers = _satusehat_headers()

	total_valid = 0
	total_rejected = 0

	for item in doc.items:
		if not item.kfa_code:
			item.validation_status = "Rejected"
			item.api_response = "KFA Code kosong. Silakan lengkapi di Item Master."
			total_rejected += 1
			continue

		# 1. Dapatkan Medication ID
		med_id = None
		item_doc = frappe.get_doc("Item", item.item_code)
		if item_doc.satusehat_id:
			med_id = item_doc.satusehat_id
			item.medication_id = med_id
		else:
			# Auto-register Medication (Opsi B)
			from clinic_satusehat.api import register_item_medication
			try:
				res = register_item_medication(item.item_code)
				if res and res.get("satusehat_id"):
					med_id = res.get("satusehat_id")
					item.medication_id = med_id
			except Exception as e:
				item.validation_status = "Rejected"
				item.api_response = f"Gagal auto-register Medication: {str(e)}"
				total_rejected += 1
				continue

		if not med_id:
			continue

		# 2. Create MedicationRequest Payload
		medreq_payload = {
			"resourceType": "MedicationRequest",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/prescription/{org_id}",
					"use": "official",
					"value": f"{docname}-{item.item_code}"
				}
			],
			"status": "completed",
			"intent": "order",
			"medicationReference": {
				"reference": f"Medication/{med_id}"
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}",
				"display": doc.patient_name
			},
			"encounter": {
				"reference": f"Encounter/{doc.satusehat_encounter_id}"
			},
			"authoredOn": datetime.now().isoformat() + "+07:00",
			"requester": {
				"reference": f"Practitioner/{doc.practitioner_ihs}"
			},
			"dosageInstruction": [
				{
					"sequence": 1,
					"text": item.dosage or "Sesuai petunjuk dokter"
				}
			]
		}

		try:
			resp2 = requests.post(f"{base_url}/MedicationRequest", json=medreq_payload, headers=headers, timeout=30)
			if resp2.status_code in [200, 201]:
				req_id = resp2.json().get("id")
				item.medication_request_id = req_id
				item.validation_status = "Valid"
				item.api_response = ""
				total_valid += 1
			else:
				item.validation_status = "Rejected"
				item.api_response = f"Gagal membuat MedicationRequest: {resp2.text}"
				total_rejected += 1
		except Exception as e:
			item.validation_status = "Rejected"
			item.api_response = f"Error MedicationRequest: {str(e)}"
			total_rejected += 1
	
	if total_rejected == 0 and total_valid > 0:
		doc.status = "Valid"
	elif total_valid == 0:
		doc.status = "Rejected"
	else:
		doc.status = "Partial"
	
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"status": doc.status}

