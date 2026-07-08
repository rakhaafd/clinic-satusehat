import frappe
from .base_builder import PayloadBuilder

class AllergyIntoleranceBuilder(PayloadBuilder):
	def build(self, doc):
		return {
			"resourceType": "AllergyIntolerance",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/allergy/{doc.organization_id}",
					"use": "official",
					"value": "ALGI-001"
				}
			],
			"clinicalStatus": {
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
						"code": "active",
						"display": "Active"
					}
				]
			},
			"verificationStatus": {
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
						"code": "confirmed",
						"display": "Confirmed"
					}
				]
			},
			"category": [
				"food"
			],
			"code": {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": "GANTI_DENGAN_KODE_SNOMED_ALERGI",
						"display": "GANTI_DENGAN_NAMA_ALERGI_SNOMED"
					}
				],
				"text": "Alergi Makanan (Contoh)"
			},
			"patient": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"recorder": {
				"reference": f"Practitioner/{doc.practitioner_ihs}"
			}
		}
