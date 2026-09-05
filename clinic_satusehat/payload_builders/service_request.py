import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime
from clinic_satusehat.satusehat_client import get_organization_id

class ServiceRequestBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		org_id = getattr(doc, "organization_id", "") or get_organization_id()
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		doc_name = getattr(doc, "name", "SR-RAD-001")
		loinc_code = getattr(doc, "loinc_code", "") or "24725-4"
		loinc_display = getattr(doc, "loinc_display", "") or "CT head"
		request_text = getattr(doc, "request_text", "") or "Pemeriksaan CT-Scan Kepala"

		return {
			"resourceType": "ServiceRequest",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/servicerequest/{org_id}",
					"value": doc_name
				}
			],
			"status": "active",
			"intent": "order",
			"category": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": "363679005",
							"display": "Imaging"
						}
					]
				}
			],
			"code": {
				"coding": [
					{
						"system": "http://loinc.org",
						"code": loinc_code,
						"display": loinc_display
					}
				],
				"text": request_text
			},
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"authoredOn": current_time,
			"requester": {
				"reference": f"Practitioner/{practitioner_ihs}"
			},
			"performer": [
				{
					"reference": f"Practitioner/{practitioner_ihs}"
				}
			]
		}
