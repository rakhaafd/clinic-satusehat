import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime, get_datetime
from clinic_satusehat.satusehat_client import get_organization_id

class MedicationRequestBuilder(PayloadBuilder):
	def build(self, doc):
		org_id = getattr(doc, "organization_id", "") or get_organization_id()
		patient_ihs = getattr(doc, "patient_ihs", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")

		med_ref_id = getattr(doc, "med_ref_id", "") or getattr(doc, "medication_id", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		doc_name = getattr(doc, "name", "RX-001")

		if not patient_ihs:
			frappe.throw("Patient IHS ID belum terisi.")
		if not practitioner_ihs:
			frappe.throw("Practitioner IHS ID belum terisi.")
		if not med_ref_id:
			frappe.throw("Medication SATUSEHAT ID belum terisi.")
		if not enc_ref_id:
			frappe.throw("Encounter SATUSEHAT ID belum terisi.")

		med_display = getattr(doc, "kfa_display", "") or getattr(doc, "item_name", "") or getattr(doc, "med_display", "") or "Medication"
		dosage_text = getattr(doc, "dosage", "") or getattr(doc, "dosage_instruction", "") or "Aturan pakai"

		authored_dt = getattr(doc, "authored_on", None) or getattr(doc, "creation", None)
		if authored_dt:
			authored_str = get_datetime(authored_dt).strftime("%Y-%m-%dT%H:%M:%S+07:00")
		else:
			authored_str = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+07:00")

		return {
			"resourceType": "MedicationRequest",
			"identifier": [{"system": f"http://sys-ids.kemkes.go.id/prescription/{org_id}", "use": "official", "value": doc_name}],
			"status": "active",
			"intent": "order",
			"category": [
				{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category", "code": "outpatient", "display": "Outpatient"}]}
			],
			"medicationReference": {"reference": f"Medication/{med_ref_id}", "display": med_display},
			"subject": {"reference": f"Patient/{patient_ihs}"},
			"encounter": {"reference": f"Encounter/{enc_ref_id}"},
			"authoredOn": authored_str,
			"requester": {"reference": f"Practitioner/{practitioner_ihs}"},
			"dosageInstruction": [
				{
					"text": dosage_text,
					"timing": {
						"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
					}
				}
			]
		}
