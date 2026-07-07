import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class ServiceRequestBuilder(PayloadBuilder):
	def build(self, doc):
		# Waktu saat ini dengan zona waktu UTC (+00:00) sesuai standar Kemenkes
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		
		return {
			"resourceType": "ServiceRequest",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/servicerequest/{doc.organization_id}",
					"value": "SR-RAD-001"
				}
			],
			"status": "active",
			"intent": "order",
			"category": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": "363679005",
							"display": "Imaging"
						}
					]
				}
			],
			"code": {
				"coding": [
					{
						"system": "http://loinc.org",
						"code": "24725-4",
						"display": "CT head"
					}
				],
				"text": "Pemeriksaan CT-Scan Kepala"
			},
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"authoredOn": current_time,
			"requester": {
				"reference": f"Practitioner/{doc.practitioner_ihs}"
			},
			"performer": [
				{
					"reference": f"Practitioner/{doc.practitioner_ihs}"
				}
			]
		}
