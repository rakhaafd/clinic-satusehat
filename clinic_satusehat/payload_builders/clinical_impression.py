import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime
from clinic_satusehat.satusehat_client import get_organization_id

class ClinicalImpressionBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		org_id = getattr(doc, "organization_id", "") or get_organization_id()
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		doc_name = getattr(doc, "name", "IMP-001")
		status = getattr(doc, "clinical_status", "completed") or getattr(doc, "status", "completed") or "completed"
		description = getattr(doc, "description", "") or "Penilaian klinis pasien"
		summary = getattr(doc, "summary", "") or "Kondisi pasien stabil setelah penanganan awal."
		note_text = getattr(doc, "note", "")

		res = {
			"resourceType": "ClinicalImpression",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/clinicalimpression/{org_id}",
					"use": "official",
					"value": doc_name
				}
			],
			"status": status,
			"description": description,
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"effectiveDateTime": current_time,
			"date": current_time,
			"assessor": {
				"reference": f"Practitioner/{practitioner_ihs}"
			},
			"summary": summary
		}
		
		if note_text:
			res["note"] = [{"text": note_text}]
			
		return res
