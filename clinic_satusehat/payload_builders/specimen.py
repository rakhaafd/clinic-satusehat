import frappe
from datetime import datetime
from .base_builder import PayloadBuilder
from frappe.utils import get_datetime
from clinic_satusehat.satusehat_client import get_organization_id

class SpecimenBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
		org_id = getattr(doc, "organization_id", "") or get_organization_id() or "10000004"
		patient_ihs = getattr(doc, "patient_ihs", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		service_request_id = getattr(doc, "service_request_id", "")
		if not service_request_id and getattr(doc, "servicerequest_satusehat", ""):
			service_request_id = frappe.db.get_value("ServiceRequest SatuSehat", doc.servicerequest_satusehat, "satusehat_id") or ""
		if not service_request_id:
			service_request_id = "GANTI_DENGAN_ID_SERVICEREQUEST_SEBELUMNYA"
			
		specimen_ident = getattr(doc, "specimen_identifier", "") or getattr(doc, "name", "SPC-12345")
		specimen_code = getattr(doc, "specimen_code", "") or "119297000"
		specimen_display = getattr(doc, "specimen_display", "") or "Blood specimen"
		
		collected_dt = getattr(doc, "collected_datetime", None)
		if collected_dt:
			collected_str = get_datetime(collected_dt).strftime("%Y-%m-%dT%H:%M:%S+00:00")
		else:
			collected_str = current_time

		return {
			"resourceType": "Specimen",
			"identifier": [
				{
					"use": "official",
					"system": f"http://sys-ids.kemkes.go.id/specimen/{org_id}",
					"value": specimen_ident
				}
			],
			"status": "available",
			"type": {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": specimen_code,
						"display": specimen_display
					}
				]
			},
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"request": [
				{
					"reference": f"ServiceRequest/{service_request_id}"
				}
			],
			"collection": {
				"collectedDateTime": collected_str,
				"collector": {
					"reference": f"Practitioner/{practitioner_ihs}"
				}
			}
		}
