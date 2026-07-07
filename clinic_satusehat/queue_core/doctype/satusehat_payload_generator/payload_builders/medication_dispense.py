import frappe
from .base_builder import PayloadBuilder

class MedicationDispenseBuilder(PayloadBuilder):
    def build(self, doc):
        encounter_doc = None
        if doc.patient_encounter:
            encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
            
        med_display = "Paracetamol"
        if encounter_doc and encounter_doc.drug_prescription:
            first_drug = encounter_doc.drug_prescription[0]
            if first_drug.drug_code:
                try:
                    item = frappe.get_doc("Item", first_drug.drug_code)
                    med_display = item.get("item_name") or med_display
                except:
                    pass

        return {
            "resourceType": "MedicationDispense",
            "identifier": [{"system": f"http://sys-ids.kemkes.go.id/prescription/{doc.organization_id}", "use": "official", "value": "DISP-001"}],
            "status": "completed",
            "medicationReference": {"reference": f"Medication/{getattr(doc, 'med_ref_id', 'GANTI_DENGAN_ID_MEDICATION_SEBELUMNYA')}", "display": med_display},
            "subject": {"reference": f"Patient/{doc.patient_ihs}"},
            "context": {"reference": f"Encounter/{getattr(doc, 'enc_ref_id', 'GANTI_DENGAN_ID_ENCOUNTER_SEBELUMNYA')}"},
            "authorizingPrescription": [{"reference": f"MedicationRequest/{getattr(doc, 'req_ref_id', 'GANTI_DENGAN_ID_MEDREQ_SEBELUMNYA')}"}]
        }
