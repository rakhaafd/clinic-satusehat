import frappe
from .base_builder import PayloadBuilder

class EpisodeOfCareBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00) 
		# We use 2024 to avoid "Future Date" errors for some Kemenkes validation profiles
		current_time = "2024-01-01T00:00:00+00:00"
		org_id = getattr(doc, "organization_id", None) or "GANTI_DENGAN_ORG_ID"

		return {
			"resourceType": "EpisodeOfCare",
			"status": "active",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/episode-of-care/{org_id}",
					"use": "official",
					"value": "EOC-2024-001"
				}
			],
			"statusHistory": [
				{
					"status": "active",
					"period": {
						"start": current_time
					}
				}
			],
			"type": [
				{
					"coding": [
						{
							"system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
							"code": getattr(doc, "type_code", "da"),
							"display": getattr(doc, "type_display", "Drug and alcohol rehabilitation")
						}
					]
				}
			],
			"patient": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"managingOrganization": {
				"reference": f"Organization/{org_id}"
			},
			"period": {
				"start": current_time
			}
		}
