import frappe
from datetime import datetime
from .base_builder import PayloadBuilder
from frappe.utils import get_datetime
from clinic_satusehat.satusehat_client import get_organization_id

class EpisodeOfCareBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
		org_id = getattr(doc, "organization_id", "") or get_organization_id() or "10000004"
		patient_ihs = getattr(doc, "patient_ihs", "")
		
		identifier_val = getattr(doc, "identifier_value", "") or getattr(doc, "name", "EOC-001")
		type_code = getattr(doc, "type_code", "") or "da"
		type_display = getattr(doc, "type_display", "") or "Drug and alcohol rehabilitation"
		
		start_date = getattr(doc, "start_date", None)
		if start_date:
			dt_str = f"{start_date} 00:00:00"
			iso_start = get_datetime(dt_str).strftime("%Y-%m-%dT%H:%M:%S+00:00")
		else:
			iso_start = current_time

		return {
			"resourceType": "EpisodeOfCare",
			"status": "active",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/episode-of-care/{org_id}",
					"use": "official",
					"value": identifier_val
				}
			],
			"statusHistory": [
				{
					"status": "active",
					"period": {
						"start": iso_start
					}
				}
			],
			"type": [
				{
					"coding": [
						{
							"system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
							"code": type_code,
							"display": type_display
						}
					]
				}
			],
			"patient": {
				"reference": f"Patient/{patient_ihs}"
			},
			"managingOrganization": {
				"reference": f"Organization/{org_id}"
			},
			"period": {
				"start": iso_start
			}
		}
