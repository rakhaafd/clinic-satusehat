# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from frappe.utils import get_datetime

class SpecimenSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("Specimen Validator", {"specimen_satusehat": self.name}):
			doc_val = frappe.new_doc("Specimen Validator")
			doc_val.specimen_satusehat = self.name
			doc_val.status = self.status
			doc_val.insert(ignore_permissions=True)

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
	doc = frappe.get_doc("Specimen SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
		
	if doc.satusehat_id:
		frappe.throw("Dokumen ini sudah terkirim ke SatuSehat.")

	# Get the ServiceRequest ID
	sr_id = frappe.db.get_value("ServiceRequest SatuSehat", doc.servicerequest_satusehat, "satusehat_id")
	if not sr_id:
		frappe.throw("ServiceRequest yang ditautkan belum memiliki SatuSehat ID. Pastikan sudah dikirim ke Kemkes.")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	headers = _satusehat_headers()

	from clinic_satusehat.queue_core.doctype.satusehat_payload_generator.payload_builders.specimen import SpecimenBuilder
	
	org_id = frappe.conf.get("satusehat_organization_id") or "10000004"
	
	class MockDoc:
		patient_ihs = doc.patient_ihs
		practitioner_ihs = doc.practitioner_ihs
		organization_id = org_id
		service_request_id = sr_id
		
	builder = SpecimenBuilder()
	payload = builder.build(MockDoc())
	
	payload["identifier"][0]["value"] = doc.specimen_identifier
	payload["type"]["coding"][0]["code"] = doc.specimen_code
	payload["type"]["coding"][0]["display"] = doc.specimen_display
	
	if doc.collected_datetime:
		dt = get_datetime(doc.collected_datetime)
		payload["collection"]["collectedDateTime"] = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
	
	try:
		resp = requests.post(f"{base_url}/Specimen", json=payload, headers=headers, timeout=30)
		
		doc.db_set("api_response", resp.text)
		
		if resp.status_code in [200, 201]:
			satusehat_id = resp.json().get("id")
			doc.db_set("satusehat_id", satusehat_id)
			frappe.db.commit()
			return {"status": resp.status_code, "message": "Berhasil mengirim Specimen."}
		else:
			return {"status": resp.status_code, "message": "Gagal mengirim Specimen. Periksa API Response."}
	except Exception as e:
		doc.db_set("api_response", str(e))
		frappe.db.commit()
		return {"status": 500, "message": str(e)}
