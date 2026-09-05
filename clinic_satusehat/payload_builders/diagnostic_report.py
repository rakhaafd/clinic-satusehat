from datetime import datetime
import frappe
from .base_builder import PayloadBuilder

class DiagnosticReportBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
		
		patient_ihs = getattr(doc, "patient_ihs", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		if not enc_ref_id and getattr(doc, "encounter_satusehat", ""):
			enc_ref_id = frappe.db.get_value("Encounter SatuSehat", doc.encounter_satusehat, "satusehat_id") or ""
			
		service_request_id = getattr(doc, "service_request_id", "")
		if not service_request_id and getattr(doc, "servicerequest_satusehat", ""):
			service_request_id = frappe.db.get_value("ServiceRequest SatuSehat", doc.servicerequest_satusehat, "satusehat_id") or ""
		if not service_request_id:
			service_request_id = "GANTI_DENGAN_ID_SERVICEREQUEST"

		specimen_id = getattr(doc, "specimen_id", "")
		if not specimen_id and getattr(doc, "specimen_satusehat", ""):
			specimen_id = frappe.db.get_value("Specimen SatuSehat", doc.specimen_satusehat, "satusehat_id") or ""
		if not specimen_id:
			specimen_id = "GANTI_DENGAN_ID_SPECIMEN"

		observation_id = getattr(doc, "observation_id", "")
		if not observation_id and getattr(doc, "observation_satusehat", ""):
			obs_ids_raw = frappe.db.get_value("Observation SatuSehat", doc.observation_satusehat, "satusehat_ids")
			if obs_ids_raw:
				import json
				try:
					obs_ids = json.loads(obs_ids_raw)
					observation_id = obs_ids[0] if obs_ids else ""
				except Exception:
					observation_id = obs_ids_raw.split(",")[0].strip()
		if not observation_id:
			observation_id = "GANTI_DENGAN_ID_OBSERVATION"

		report_code = getattr(doc, "report_code", "") or "11477-7"
		report_display = getattr(doc, "report_display", "") or "Microscopic observation [Identifier] in Sputum by Acid fast stain"
		conclusion_code = getattr(doc, "conclusion_code", "") or "260347006"
		conclusion_display = getattr(doc, "conclusion_display", "") or "Positive"

		return {
			"resourceType": "DiagnosticReport",
			"status": "final",
			"category": [
				{
					"coding": [
						{
							"system": "http://terminology.hl7.org/CodeSystem/v2-0074",
							"code": "LAB",
							"display": "Laboratory"
						}
					]
				}
			],
			"code": {
				"coding": [
					{
						"system": "http://loinc.org",
						"code": report_code,
						"display": report_display
					}
				]
			},
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"effectiveDateTime": current_time,
			"issued": current_time,
			"performer": [
				{
					"reference": f"Practitioner/{practitioner_ihs}"
				}
			],
			"basedOn": [
				{
					"reference": f"ServiceRequest/{service_request_id}"
				}
			],
			"specimen": [
				{
					"reference": f"Specimen/{specimen_id}"
				}
			],
			"result": [
				{
					"reference": f"Observation/{observation_id}"
				}
			],
			"conclusionCode": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": conclusion_code,
							"display": conclusion_display
						}
					]
				}
			]
		}
