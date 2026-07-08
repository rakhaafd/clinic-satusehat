# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json

class DiagnosticReportSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("DiagnosticReport Validator", {"diagnosticreport_satusehat": self.name}):
			doc_val = frappe.new_doc("DiagnosticReport Validator")
			doc_val.diagnosticreport_satusehat = self.name
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
	doc = frappe.get_doc("DiagnosticReport SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
		
	if doc.satusehat_id:
		frappe.throw("Dokumen ini sudah terkirim ke SatuSehat.")

	sr_id = frappe.db.get_value("ServiceRequest SatuSehat", doc.servicerequest_satusehat, "satusehat_id")
	if not sr_id:
		frappe.throw("ServiceRequest yang ditautkan belum memiliki SatuSehat ID.")

	sp_id = frappe.db.get_value("Specimen SatuSehat", doc.specimen_satusehat, "satusehat_id")
	if not sp_id:
		frappe.throw("Specimen yang ditautkan belum memiliki SatuSehat ID.")

	obs_ids_raw = frappe.db.get_value("Observation SatuSehat", doc.observation_satusehat, "satusehat_ids")
	if not obs_ids_raw:
		frappe.throw("Observation yang ditautkan belum memiliki SatuSehat ID.")
	
	# Parse obs_id in case it is a JSON array string, or a comma-separated string
	import json
	try:
		obs_ids = json.loads(obs_ids_raw)
		obs_id = obs_ids[0] if obs_ids else ""
	except Exception:
		obs_id = obs_ids_raw.split(",")[0].strip()
		
	if not obs_id:
		frappe.throw("Observation yang ditautkan belum memiliki SatuSehat ID yang valid.")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	headers = _satusehat_headers()

	from clinic_satusehat.queue_core.doctype.satusehat_payload_generator.payload_builders.diagnostic_report import DiagnosticReportBuilder
	
	class MockDoc:
		patient_ihs = doc.patient_ihs
		practitioner_ihs = doc.practitioner_ihs
		enc_ref_id = frappe.db.get_value("Encounter SatuSehat", doc.encounter_satusehat, "satusehat_id")
		service_request_id = sr_id
		specimen_id = sp_id
		observation_id = obs_id
		
		def get(self, key, default=None):
			return getattr(self, key, default)
			
	builder = DiagnosticReportBuilder()
	payload = builder.build(MockDoc())
	
	payload["code"]["coding"][0]["code"] = doc.report_code
	payload["code"]["coding"][0]["display"] = doc.report_display
	payload["conclusionCode"][0]["coding"][0]["code"] = doc.conclusion_code
	payload["conclusionCode"][0]["coding"][0]["display"] = doc.conclusion_display
	
	try:
		doc.db_set("payload_json", json.dumps(payload, indent=2))
		resp = requests.post(f"{base_url}/DiagnosticReport", json=payload, headers=headers, timeout=30)
		
		doc.db_set("api_response", resp.text)
		
		if resp.status_code in [200, 201]:
			satusehat_id = resp.json().get("id")
			doc.db_set("satusehat_id", satusehat_id)
			frappe.db.commit()
			return {"status": resp.status_code, "message": "Berhasil mengirim DiagnosticReport."}
		else:
			return {"status": resp.status_code, "message": "Gagal mengirim DiagnosticReport. Periksa API Response."}
	except Exception as e:
		doc.db_set("api_response", str(e))
		frappe.db.commit()
		return {"status": 500, "message": str(e)}
