# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
from datetime import datetime

class MedicationDispenseSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("MedicationDispense Validator", {"medication_dispense_satusehat": self.name}):
			doc_val = frappe.new_doc("MedicationDispense Validator")
			doc_val.medication_dispense_satusehat = self.name
			doc_val.status = self.status
			doc_val.insert(ignore_permissions=True)

	@frappe.whitelist()
	def fetch_drugs_from_request(self):
		if not self.medication_request_satusehat:
			frappe.throw("Pilih MedicationRequest SatuSehat terlebih dahulu.")
		
		req_doc = frappe.get_doc("MedicationRequest SatuSehat", self.medication_request_satusehat)
		
		# Only fetch items that successfully got a medication_request_id
		self.set("items", [])
		count = 0
		for req_item in req_doc.items:
			if req_item.medication_request_id and req_item.validation_status == "Valid":
				self.append("items", {
					"item_code": req_item.item_code,
					"item_name": req_item.item_name,
					"kfa_code": req_item.kfa_code,
					"kfa_display": req_item.kfa_display,
					"dosage": req_item.dosage,
					"medication_id": req_item.medication_id,
					"medication_request_id": req_item.medication_request_id,
					"validation_status": "Waiting"
				})
				count += 1
		
		if count == 0:
			frappe.msgprint("Tidak ditemukan obat yang berstatus Valid (memiliki ID Resep) pada dokumen tersebut.")
		else:
			frappe.msgprint(f"Berhasil menarik {count} obat.")
			
		self.save()

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
def send_to_satusehat(docname):
	doc = frappe.get_doc("MedicationDispense SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
	
	if not doc.items:
		frappe.throw("Tidak ada obat yang akan dikirim. Silakan Fetch terlebih dahulu.")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	org_id = frappe.conf.get("satusehat_organization_id")
	headers = _satusehat_headers()

	total_valid = 0
	total_rejected = 0

	for item in doc.items:
		# Lewati yang sudah terkirim atau ditolak permanen
		if item.validation_status == "Valid" and item.medication_dispense_id:
			total_valid += 1
			continue
			
		if not item.medication_request_id:
			item.validation_status = "Rejected"
			item.api_response = "MedicationRequest ID kosong."
			total_rejected += 1
			continue

		# Create MedicationDispense Payload
		dispense_payload = {
			"resourceType": "MedicationDispense",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/prescription/{org_id}",
					"use": "official",
					"value": f"{docname}-{item.item_code}"
				}
			],
			"status": "completed",
			"medicationReference": {
				"reference": f"Medication/{item.medication_id}"
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}",
				"display": doc.patient_name
			},
			"context": {
				"reference": f"Encounter/{doc.satusehat_encounter_id}"
			},
			"whenHandedOver": datetime.now().isoformat() + "+07:00",
			"authorizingPrescription": [
				{
					"reference": f"MedicationRequest/{item.medication_request_id}"
				}
			],
			"dosageInstruction": [
				{
					"sequence": 1,
					"text": item.dosage or "Aturan pakai"
				}
			]
		}

		try:
			doc.db_set("payload_json", json.dumps(payload, indent=2))
		resp = requests.post(f"{base_url}/MedicationDispense", json=dispense_payload, headers=headers, timeout=30)
			
			item.api_response = resp.text
			
			if resp.status_code in [200, 201]:
				dispense_id = resp.json().get("id")
				item.medication_dispense_id = dispense_id
				item.validation_status = "Valid"
				total_valid += 1
			else:
				item.validation_status = "Rejected"
				total_rejected += 1
		except Exception as e:
			item.validation_status = "Rejected"
			item.api_response = str(e)
			total_rejected += 1

	doc.save(ignore_permissions=True)
	
	if total_rejected == 0 and total_valid > 0:
		frappe.db.set_value("MedicationDispense SatuSehat", docname, "status", "Valid")
		return {"status": 200, "message": "Semua obat berhasil diserahkan ke SatuSehat!"}
	elif total_valid > 0 and total_rejected > 0:
		frappe.db.set_value("MedicationDispense SatuSehat", docname, "status", "Partial")
		return {"status": 206, "message": f"{total_valid} obat berhasil, {total_rejected} gagal."}
	else:
		frappe.db.set_value("MedicationDispense SatuSehat", docname, "status", "Rejected")
		return {"status": 400, "message": "Gagal menyerahkan obat. Periksa tabel item untuk log error."}
