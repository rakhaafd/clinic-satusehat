import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class ImagingStudyBuilder(PayloadBuilder):
	def build(self, doc):
		# Default placeholder time in ISO 8601 UTC timezone (+00:00) as required by SatuSehat
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		
		return {
			"resourceType": "ImagingStudy",
			"identifier": [
				{
					"use": "official",
					"system": "urn:dicom:uid",
					"value": "urn:oid:1.2.840.113619.2.55.3.4271045733.996.1449464144.595"
				}
			],
			"status": "available",
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"started": current_time,
			"basedOn": [
				{
					"reference": f"ServiceRequest/{doc.srv_ref_id}"
				}
			],
			"modality": [
				{
					"system": "http://dicom.nema.org/resources/ontology/DCM",
					"code": "CT",
					"display": "Computed Tomography"
				}
			],
			"numberOfSeries": 1,
			"numberOfInstances": 1,
			"series": [
				{
					"uid": "1.2.840.113619.2.55.3.4271045733.996.1449464144.596",
					"modality": {
						"system": "http://dicom.nema.org/resources/ontology/DCM",
						"code": "CT",
						"display": "Computed Tomography"
					},
					"instance": [
						{
							"uid": "1.2.840.113619.2.55.3.4271045733.996.1449464144.597",
							"sopClass": {
								"system": "urn:ietf:rfc:3986",
								"code": "urn:oid:1.2.840.10008.5.1.4.1.1.2"
							},
							"number": 1
						}
					]
				}
			]
		}
