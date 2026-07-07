import frappe
from .base_builder import PayloadBuilder

class ConditionBuilder(PayloadBuilder):
    def build(self, doc):
        encounter_doc = None
        if doc.patient_encounter:
            encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
            
        icd_code = doc.get("diagnostic_code") or "K04.1"
        diagnosis_display = "Diagnosis"
        
        if encounter_doc and encounter_doc.diagnosis:
            first_diagnosis = encounter_doc.diagnosis[0]
            if first_diagnosis.diagnosis:
                try:
                    diag = frappe.get_doc("Diagnosis", first_diagnosis.diagnosis)
                    icd_code = diag.get("icd10_code") or diag.get("diagnosis_code") or icd_code
                    diagnosis_display = diag.get("diagnosis_name") or diag.get("description") or diagnosis_display
                except:
                    pass

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
            "subject": {"reference": f"Patient/{doc.patient_ihs}", "display": "Pasien"},
            "encounter": {"reference": f"Encounter/{getattr(doc, 'enc_ref_id', 'GANTI_DENGAN_ID_ENCOUNTER_SEBELUMNYA')}"}
        }
