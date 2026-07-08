import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class QuestionnaireResponseBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00) 
		# We use 2024 to avoid "Future Date" errors for some Kemenkes validation profiles
		current_time = "2024-01-01T00:00:00+00:00"
		
		return {
			"resourceType": "QuestionnaireResponse",
			"status": "completed",
			"questionnaire": "https://fhir.kemkes.go.id/Questionnaire/Q0002",
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"authored": current_time,
			"author": {
				"reference": f"Practitioner/{doc.practitioner_ihs}"
			},
			"source": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"item": [
				{
					"linkId": "1",
					"text": "Apakah keluhan utama pasien?",
					"answer": [
						{
							"valueString": "Pusing dan mual"
						}
					]
				},
				{
					"linkId": "2",
					"text": "Apakah ada riwayat alergi?",
					"answer": [
						{
							"valueBoolean": False
						}
					]
				}
			]
		}
