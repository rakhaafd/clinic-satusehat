import frappe
from .base_builder import PayloadBuilder

class CarePlanBuilder(PayloadBuilder):
	def build(self, doc):
		return {
			"resourceType": "CarePlan",
			"status": "active",
			"intent": "plan",
			"title": "Rencana Perawatan Lanjutan Pasien",
			"description": "Pasien disarankan istirahat cukup, menjaga pola makan, dan meminum obat sesuai dosis. Kembali kontrol jika gejala tidak membaik dalam 3 hari.",
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"author": {
				"reference": f"Practitioner/{doc.practitioner_ihs}"
			},
			"category": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": "736372004",
							"display": "Discharge care plan"
						}
					]
				}
			]
		}
