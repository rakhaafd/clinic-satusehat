import frappe
from .base_builder import PayloadBuilder
from datetime import datetime

class ProcedureBuilder(PayloadBuilder):
	def build(self, doc):
		patient_ihs = getattr(doc, "patient_ihs", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		encounter_id = (
			getattr(doc, "satusehat_encounter_id", "")
			or getattr(doc, "enc_ref_id", "")
			or getattr(doc, "enc_ref_id_override", "")
		)

		if (not patient_ihs or not practitioner_ihs or not encounter_id) and getattr(doc, "encounter_satusehat", None):
			try:
				enc_doc = frappe.get_doc("Encounter SatuSehat", doc.encounter_satusehat)
				patient_ihs = patient_ihs or enc_doc.patient_ihs
				practitioner_ihs = practitioner_ihs or enc_doc.practitioner_ihs
				encounter_id = encounter_id or enc_doc.satusehat_id
			except Exception:
				pass

		procedure_code = getattr(doc, "procedure_code", "") or getattr(doc, "code", "") or "87.44"
		procedure_display = getattr(doc, "procedure_display", "") or getattr(doc, "display", "") or "Routine chest x-ray"

		performed_time = getattr(doc, "performed_date_time", None) or getattr(doc, "posting_date", None)
		if performed_time:
			current_time = str(performed_time).replace(" ", "T") + "+07:00"
		else:
			current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")

		return {
			"resourceType": "Procedure",
			"status": getattr(doc, "procedure_status", "completed") or "completed",
			"category": {
				"coding": [{"system": "http://snomed.info/sct", "code": "103693007", "display": "Diagnostic procedure"}],
				"text": "Diagnostic procedure"
			},
			"code": {
				"coding": [
					{
						"system": "http://hl7.org/fhir/sid/icd-9-cm",
						"code": procedure_code,
						"display": procedure_display
					}
				]
			},
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{encounter_id}"
			},
			"performedDateTime": current_time,
			"performer": [
				{
					"actor": {
						"reference": f"Practitioner/{practitioner_ihs}"
					}
				}
			]
		}
