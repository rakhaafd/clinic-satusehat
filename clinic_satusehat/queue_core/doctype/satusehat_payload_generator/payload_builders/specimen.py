import frappe
from .base_builder import PayloadBuilder

class SpecimenBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00) 
		# We use 2024 to avoid "Future Date" errors for some Kemenkes validation profiles
		current_time = "2024-01-01T00:00:00+00:00"
		# Mengambil identifier spesimen (dummy)
		org_id = getattr(doc, "organization_id", None) or "GANTI_DENGAN_ORG_ID"
		
		# Specimen memerlukan request yang menunjuk ke ServiceRequest
		# Kita akan menggunakan service_request_id jika ada, atau nilai dummy
		service_request_id = getattr(doc, "service_request_id", None) or "GANTI_DENGAN_ID_SERVICEREQUEST_SEBELUMNYA"

		return {
			"resourceType": "Specimen",
			"identifier": [
				{
					"use": "official",
					"system": f"http://sys-ids.kemkes.go.id/specimen/{org_id}",
					"value": "SPC-12345"
				}
			],
			"status": "available",
			"type": {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": "119297000",
						"display": "Blood specimen"
					}
				]
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"request": [
				{
					"reference": f"ServiceRequest/{service_request_id}"
				}
			],
			"collection": {
				"collectedDateTime": current_time,
				"collector": {
					"reference": f"Practitioner/{doc.practitioner_ihs}"
				}
			}
		}
