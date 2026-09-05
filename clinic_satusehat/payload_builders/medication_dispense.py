import frappe
from .base_builder import PayloadBuilder
from clinic_satusehat.satusehat_client import get_organization_id

class MedicationDispenseBuilder(PayloadBuilder):
	def build(self, doc):
		org_id = getattr(doc, "organization_id", "") or get_organization_id()
		patient_ihs = getattr(doc, "patient_ihs", "")

		med_ref_id = getattr(doc, "med_ref_id", "") or getattr(doc, "medication_id", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		req_ref_id = getattr(doc, "req_ref_id", "") or getattr(doc, "medication_request_id", "")
		doc_name = getattr(doc, "name", "DISP-001")

		if not patient_ihs:
			frappe.throw("Patient IHS ID belum terisi.")
		if not med_ref_id:
			frappe.throw("Medication SATUSEHAT ID belum terisi.")
		if not enc_ref_id:
			frappe.throw("Encounter SATUSEHAT ID belum terisi.")
		if not req_ref_id:
			frappe.throw("MedicationRequest SATUSEHAT ID belum terisi.")

		med_display = getattr(doc, "kfa_display", "") or getattr(doc, "item_name", "") or getattr(doc, "med_display", "") or "Medication"

		return {
			"resourceType": "MedicationDispense",
			"identifier": [{"system": f"http://sys-ids.kemkes.go.id/prescription/{org_id}", "use": "official", "value": doc_name}],
			"status": "completed",
			"medicationReference": {"reference": f"Medication/{med_ref_id}", "display": med_display},
			"subject": {"reference": f"Patient/{patient_ihs}"},
			"context": {"reference": f"Encounter/{enc_ref_id}"},
			"authorizingPrescription": [{"reference": f"MedicationRequest/{req_ref_id}"}]
		}
