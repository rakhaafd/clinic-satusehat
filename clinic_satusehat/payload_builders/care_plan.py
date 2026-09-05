import frappe
from .base_builder import PayloadBuilder

class CarePlanBuilder(PayloadBuilder):
	def build(self, doc):
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		title = getattr(doc, "title", "") or "Rencana Perawatan Lanjutan Pasien"
		description = getattr(doc, "description", "") or "Pasien disarankan istirahat cukup, menjaga pola makan, dan meminum obat sesuai dosis."

		return {
			"resourceType": "CarePlan",
			"status": "active",
			"intent": "plan",
			"title": title,
			"description": description,
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"author": {
				"reference": f"Practitioner/{practitioner_ihs}"
			},
			"category": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": "736372004",
							"display": "Discharge care plan"
						}
					]
				}
			]
		}
