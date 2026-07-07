import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class ClinicalImpressionBuilder(PayloadBuilder):
	def build(self, doc):
		# Waktu saat ini dengan zona waktu UTC (+00:00) sesuai standar Kemenkes
		current_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
		
		return {
			"resourceType": "ClinicalImpression",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/clinicalimpression/{doc.organization_id}",
					"use": "official",
					"value": "IMP-001"
				}
			],
			"status": "completed",
			"description": "Penilaian klinis pasien",
			"subject": {
				"reference": f"Patient/{doc.patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{doc.enc_ref_id}"
			},
			"effectiveDateTime": current_time,
			"date": current_time,
			"assessor": {
				"reference": f"Practitioner/{doc.practitioner_ihs}"
			},
			"summary": "Kondisi pasien stabil setelah penanganan awal.",
			"note": [
				{
					"text": "Catatan tambahan: Pasien disarankan istirahat."
				}
			]
		}
