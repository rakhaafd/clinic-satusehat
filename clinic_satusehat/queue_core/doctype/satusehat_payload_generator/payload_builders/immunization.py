import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class ImmunizationBuilder(PayloadBuilder):
	def build(self, doc):
		# Waktu saat ini dengan zona waktu UTC (+00:00) sesuai standar Kemenkes
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		
		return {
			"resourceType": "Immunization",
			"status": "completed",
			"vaccineCode": {
				"coding": [
					{
						"system": "http://sys-ids.kemkes.go.id/kfa",
						"code": "93001282", 
						"display": "Vaksin COVID-19"
					}
				]
			},
			"patient": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"occurrenceDateTime": "2024-01-01T00:00:00+00:00",
			"primarySource": True,
			"lotNumber": "LOT12345",
			"expirationDate": "2025-01-01",
			"performer": [
				{
					"function": {
						"coding": [
							{
								"system": "http://terminology.hl7.org/CodeSystem/v2-0443",
								"code": "AP",
								"display": "Administering Provider"
							}
						]
					},
					"actor": {
						"reference": f"Practitioner/{doc.practitioner_ihs}"
					}
				}
			],
			"reasonCode": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": "429060002",
							"display": "Procedure to prevent disease"
						}
					]
				}
			],
			"protocolApplied": [
				{
					"doseNumberPositiveInt": 1
				}
			]
		}
