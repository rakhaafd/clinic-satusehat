import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class ImagingStudyBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		srv_ref_id = getattr(doc, "srv_ref_id", "") or getattr(doc, "satusehat_servicerequest_id", "") or "GANTI_DENGAN_ID_SERVICEREQUEST"
		
		modality_code = getattr(doc, "modality_code", "") or "CT"
		modality_display = getattr(doc, "modality_display", "") or "Computed Tomography"
		
		dicom_uid = getattr(doc, "dicom_uid", "") or "urn:oid:1.2.840.113619.2.55.3.4271045733.996.1449464144.595"
		pure_uid = dicom_uid.replace("urn:oid:", "")

		return {
			"resourceType": "ImagingStudy",
			"identifier": [
				{
					"use": "official",
					"system": "urn:dicom:uid",
					"value": dicom_uid
				}
			],
			"status": "available",
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"started": current_time,
			"basedOn": [
				{
					"reference": f"ServiceRequest/{srv_ref_id}"
				}
			],
			"modality": [
				{
					"system": "http://dicom.nema.org/resources/ontology/DCM",
					"code": modality_code,
					"display": modality_display
				}
			],
			"numberOfSeries": 1,
			"numberOfInstances": 1,
			"series": [
				{
					"uid": pure_uid,
					"modality": {
						"system": "http://dicom.nema.org/resources/ontology/DCM",
						"code": modality_code,
						"display": modality_display
					},
					"instance": [
						{
							"uid": f"{pure_uid}.1",
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
