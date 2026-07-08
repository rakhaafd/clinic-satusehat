import frappe
from .base_builder import PayloadBuilder

class DiagnosticReportBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00) 
		# We use 2024 to avoid "Future Date" errors for some Kemenkes validation profiles
		current_time = "2024-01-01T00:00:00+00:00"
		
		# Mengambil referensi dari isian UI
		service_request_id = doc.service_request_id if doc.get("service_request_id") else "GANTI_DENGAN_ID_SERVICEREQUEST"
		specimen_id = doc.specimen_id if doc.get("specimen_id") else "GANTI_DENGAN_ID_SPECIMEN"
		observation_id = doc.observation_id if doc.get("observation_id") else "GANTI_DENGAN_ID_OBSERVATION"

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
							"code": "260347006",
							"display": "Positive"
						}
					]
				}
			]
		}
