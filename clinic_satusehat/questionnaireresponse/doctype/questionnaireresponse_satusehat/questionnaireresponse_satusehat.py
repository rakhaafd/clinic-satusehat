# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from frappe.utils import get_datetime

class QuestionnaireResponseSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("QuestionnaireResponse Validator", {"questionnaireresponse_satusehat": self.name}):
			doc_val = frappe.new_doc("QuestionnaireResponse Validator")
			doc_val.questionnaireresponse_satusehat = self.name
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
	doc = frappe.get_doc("QuestionnaireResponse SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
		
	if doc.satusehat_id:
		frappe.throw("Dokumen ini sudah terkirim ke SatuSehat.")

	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	headers = _satusehat_headers()

	from clinic_satusehat.queue_core.doctype.satusehat_payload_generator.payload_builders.questionnaire_response import QuestionnaireResponseBuilder
	
	class MockDoc:
		patient_ihs = doc.patient_ihs
		enc_ref_id = doc.satusehat_encounter_id
		practitioner_ihs = doc.practitioner_ihs
		
	builder = QuestionnaireResponseBuilder()
	payload = builder.build(MockDoc())
	
	payload["questionnaire"] = doc.questionnaire_url
	
	# Convert datetime to SatuSehat ISO 8601 format
	if doc.authored_datetime:
		dt = get_datetime(doc.authored_datetime)
		payload["authored"] = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
	
	# Mapping answers to specific linkIds based on blueprint
	for item in payload.get("item", []):
		if item.get("linkId") == "1":
			item["answer"][0]["valueString"] = doc.keluhan_utama
		elif item.get("linkId") == "2":
			# doc.riwayat_alergi is 1 (True) or 0 (False)
			item["answer"][0]["valueBoolean"] = bool(doc.riwayat_alergi)

	try:
		doc.db_set("payload_json", json.dumps(payload, indent=2))
		resp = requests.post(f"{base_url}/QuestionnaireResponse", json=payload, headers=headers, timeout=30)
		
		doc.db_set("api_response", resp.text)
		
		if resp.status_code in [200, 201]:
			satusehat_id = resp.json().get("id")
			doc.db_set("satusehat_id", satusehat_id)
			frappe.db.commit()
			return {"status": resp.status_code, "message": "Berhasil mengirim QuestionnaireResponse."}
		else:
			return {"status": resp.status_code, "message": "Gagal mengirim QuestionnaireResponse. Periksa API Response."}
	except Exception as e:
		doc.db_set("api_response", str(e))
		frappe.db.commit()
		return {"status": 500, "message": str(e)}
