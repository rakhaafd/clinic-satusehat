import frappe
from .base_builder import PayloadBuilder

class ProcedureBuilder(PayloadBuilder):
	def build(self, doc):
		# Waktu prosedur, gunakan tahun 2024 untuk menghindari isu "Future Date" di Kemenkes
		current_time = "2024-01-01T00:00:00+00:00"

		return {
			"resourceType": "Procedure",
			"status": "completed",
			"code": {
				"coding": [
					{
						"system": "http://hl7.org/fhir/sid/icd-9-cm",
						"code": "87.44",
						"display": "Routine chest x-ray, so described"
					}
				]
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"performedDateTime": current_time,
			"performer": [
				{
					"actor": {
						"reference": f"Practitioner/{doc.practitioner_ihs}"
					}
				}
			]
		}
