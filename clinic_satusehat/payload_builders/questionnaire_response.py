import frappe
from datetime import datetime
from .base_builder import PayloadBuilder
from frappe.utils import get_datetime

class QuestionnaireResponseBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
		
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		questionnaire_url = getattr(doc, "questionnaire_url", "") or "https://fhir.kemkes.go.id/Questionnaire/Q0002"
		
		authored_dt = getattr(doc, "authored_datetime", None)
		if authored_dt:
			authored_str = get_datetime(authored_dt).strftime("%Y-%m-%dT%H:%M:%S+00:00")
		else:
			authored_str = current_time
			
		keluhan_utama = getattr(doc, "keluhan_utama", "") or "Pusing dan mual"
		riwayat_alergi = bool(getattr(doc, "riwayat_alergi", False))

		return {
			"resourceType": "QuestionnaireResponse",
			"status": "completed",
			"questionnaire": questionnaire_url,
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"authored": authored_str,
			"author": {
				"reference": f"Practitioner/{practitioner_ihs}"
			},
			"source": {
				"reference": f"Patient/{patient_ihs}"
			},
			"item": [
				{
					"linkId": "1",
					"text": "Apakah keluhan utama pasien?",
					"answer": [
						{
							"valueString": keluhan_utama
						}
					]
				},
				{
					"linkId": "2",
					"text": "Apakah ada riwayat alergi?",
					"answer": [
						{
							"valueBoolean": riwayat_alergi
						}
					]
				}
			]
		}
