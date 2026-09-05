import frappe
from datetime import datetime
from .base_builder import PayloadBuilder
from frappe.utils import get_datetime

class MedicationStatementBuilder(PayloadBuilder):
	def build(self, doc):
		current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
		
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		
		medication_code = getattr(doc, "medication_code", "") or "93002313"
		medication_display = getattr(doc, "medication_display", "") or "Paracetamol 500 mg Tablet (PAMOL)"
		
		date_asserted = getattr(doc, "date_asserted", None)
		if date_asserted:
			asserted_str = get_datetime(date_asserted).strftime("%Y-%m-%dT%H:%M:%S+00:00")
		else:
			asserted_str = current_time
			
		note_text = getattr(doc, "note", "")

		res = {
			"resourceType": "MedicationStatement",
			"status": "active",
			"category": {
				"coding": [
					{
						"system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
						"code": "community",
						"display": "Community"
					}
				]
			},
			"medicationCodeableConcept": {
				"coding": [
					{
						"system": "http://sys-ids.kemkes.go.id/kfa",
						"code": medication_code, 
						"display": medication_display
					}
				]
			},
			"subject": {
				"reference": f"Patient/{patient_ihs}"
			},
			"context": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"dateAsserted": asserted_str,
			"informationSource": {
				"reference": f"Patient/{patient_ihs}"
			}
		}
		
		if note_text:
			res["note"] = [{"text": note_text}]
			
		return res
