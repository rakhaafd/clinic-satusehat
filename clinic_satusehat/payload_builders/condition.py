import frappe
from .base_builder import PayloadBuilder

class ConditionBuilder(PayloadBuilder):
	def build(self, doc):
		encounter_doc = None
		if getattr(doc, "patient_encounter", None):
			try:
				encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
			except Exception:
				pass
			
		icd_code = getattr(doc, "icd_code", "") or getattr(doc, "icd10_code", "") or getattr(doc, "diagnostic_code", "")
		diagnosis_display = getattr(doc, "diagnosis_display", "") or getattr(doc, "icd10_display", "")
		
		if not icd_code and encounter_doc and encounter_doc.diagnosis:
			first_diagnosis = encounter_doc.diagnosis[0]
			if first_diagnosis.diagnosis:
				try:
					diag = frappe.get_doc("Diagnosis", first_diagnosis.diagnosis)
					icd_code = diag.get("icd10_code") or diag.get("diagnosis_code") or icd_code
					diagnosis_display = diag.get("diagnosis_name") or diag.get("description") or diagnosis_display
				except Exception:
					pass

		icd_code = icd_code or "Z00.0"
		diagnosis_display = diagnosis_display or "General medical examination"
		
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "satusehat_encounter_id", "") or getattr(doc, "enc_ref_id", "")

		return {
			"resourceType": "Condition",
			"clinicalStatus": {
				"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active", "display": "Active"}]
			},
			"category": [
				{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis", "display": "Encounter Diagnosis"}]}
			],
			"code": {
				"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": icd_code, "display": diagnosis_display}]
			},
			"subject": {"reference": f"Patient/{patient_ihs}", "display": getattr(doc, "patient_name", "Pasien")},
			"encounter": {"reference": f"Encounter/{enc_ref_id}"}
		}
