import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class MedicationStatementBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00) 
		# We use 2024 to avoid "Future Date" errors for some Kemenkes validation profiles
		current_time = "2024-01-01T00:00:00+00:00"
		
		return {
			"resourceType": "MedicationStatement",
			"status": "active",
			"category": {
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
						"code": "community",
						"display": "Community"
					}
				]
			},
			"medicationCodeableConcept": {
				"coding": [
					{
						"system": "http://sys-ids.kemkes.go.id/kfa",
						"code": "93002313", 
						"display": "Paracetamol 500 mg Tablet (PAMOL)"
					}
				]
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"context": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"dateAsserted": current_time,
			"informationSource": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"note": [
				{
					"text": "Pasien menyatakan rutin mengonsumsi obat ini jika demam."
				}
			]
		}
