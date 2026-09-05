import frappe
from .base_builder import PayloadBuilder
from clinic_satusehat.satusehat_client import get_organization_id

class AllergyIntoleranceBuilder(PayloadBuilder):
	def build(self, doc):
		org_id = getattr(doc, "organization_id", "") or get_organization_id()
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		doc_name = getattr(doc, "name", "ALGI-001")
		clinical_status = getattr(doc, "clinical_status", "active") or "active"
		verification_status = getattr(doc, "verification_status", "confirmed") or "confirmed"
		category = getattr(doc, "category", "food") or "food"
		snomed_code = getattr(doc, "snomed_code", "") or "GANTI_DENGAN_KODE_SNOMED_ALERGI"
		snomed_display = getattr(doc, "snomed_display", "") or "GANTI_DENGAN_NAMA_ALERGI_SNOMED"
		allergy_text = getattr(doc, "allergy_text", "") or snomed_display

		return {
			"resourceType": "AllergyIntolerance",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/allergy/{org_id}",
					"use": "official",
					"value": doc_name
				}
			],
			"clinicalStatus": {
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
						"code": clinical_status,
						"display": clinical_status.title()
					}
				]
			},
			"verificationStatus": {
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
						"code": verification_status,
						"display": verification_status.title()
					}
				]
			},
			"category": [
				category
			],
			"code": {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": snomed_code,
						"display": snomed_display
					}
				],
				"text": allergy_text
			},
			"patient": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"recorder": {
				"reference": f"Practitioner/{practitioner_ihs}"
			}
		}
