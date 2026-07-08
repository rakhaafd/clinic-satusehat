import frappe
from .base_builder import PayloadBuilder

class ObservationBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00)
		current_time = "2024-01-01T00:00:00+00:00"

		return {
			"resourceType": "Observation",
			"status": "final",
			"category": [
				{
					"coding": [
						{
							"system": "http://terminology.hl7.org/CodeSystem/observation-category",
							"code": "laboratory",
							"display": "Laboratory"
						}
					]
				}
			],
			"code": {
				"coding": [
					{
						"system": "http://loinc.org",
						"code": "11477-7",
						"display": "Microscopic observation [Identifier] in Sputum by Acid fast stain"
					}
				]
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"effectiveDateTime": current_time,
			"issued": current_time,
			"performer": [
				{
					"reference": f"Practitioner/{doc.practitioner_ihs}"
				}
			],
			"valueCodeableConcept": {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": "260347006",
						"display": "Positive"
					}
				]
			}
		}
